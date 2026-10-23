# IcapsQ Voting Workflows

These diagrams describe the current poll voting implementation shared by the Android app and website. They cover sign-in, ballot recovery, verification, database recording, duplicate protection, and the voted display.

## 1. Request routing and shared data

The website sends same-origin API requests through Nginx. The Android release uses the public API gateway. Nginx can route to either FastAPI container; both containers mount the same Docker volume containing SQLite.

```mermaid
flowchart LR
    app[Android app] -->|HTTPS API request| gateway[Nginx API gateway]
    web[Website] -->|Same-origin API request| gateway

    gateway -->|Upstream and retry| primary[FastAPI primary]
    gateway -->|Upstream and retry| replica[FastAPI replica]

    primary --> shared[(Shared Docker volume<br/>SQLite database)]
    replica --> shared

    shared --> users[Users<br/>account records]
    shared --> votes[VoteTransactions<br/>ballot and selected option]
    shared --> claims[BallotIdentityClaims<br/>unique identity claims]
    shared --> polls[Polls and PollOptions<br/>status and tallies]
```

## 2. Sign-in and restoring the VOTED badge

An account-linked vote can be restored without an ID stored on the phone. The client sends its bearer token; the API reads the account ID (`sub`) from the verified token and looks up that account's ballot for the poll.

```mermaid
flowchart TD
    start[Open polls] --> session{Valid sign-in token?}
    session -- No --> signin[Sign in to enable voting]
    signin --> start
    session -- Yes --> status[Request vote status with bearer token]
    status --> api[API verifies token and reads account ID]
    api --> lookup[Look up account claim and ballot in shared database]
    lookup --> voted{Ballot found?}
    voted -- Yes --> restore[Restore selected option and VOTED badge]
    restore --> lock[Disable all options for this poll]
    voted -- No --> eligible[Show poll as not yet voted]
    eligible --> choose[Allow voter to select an option]
    status -->|Connection or server error| retry[Keep vote unconfirmed; retry status check]
```

If no account ballot exists, a first-time vote still requires voter details. If a historical ballot was stored only by National ID and is not linked to the account, the API can find it only when that same ID is supplied for the identity check.

On Android, a locally cached account vote can preserve the badge during a temporary status outage. That cache is account-scoped and is only a display fallback; the database remains authoritative. The website checks the API when loading and again before submitting.

## 3. Casting a first vote

The app and website perform the same server checks. Their screens gather the details at slightly different times, but the API is the final authority for eligibility, county match, and duplicate prevention.

```mermaid
flowchart TD
    select[Select a poll option] --> auth{Signed in?}
    auth -- No --> stop[Ask voter to sign in]
    auth -- Yes --> prior[Check ballot status for signed-in account]
    prior --> already{Already voted?}
    already -- Yes --> restore[Restore saved option and VOTED badge; stop]
    already -- No --> details[Collect any missing name, National ID, DOB, and county]
    details --> idcheck[Check ballot history by supplied ID]
    idcheck --> idused{ID already used on this poll?}
    idused -- Yes --> restore
    idused -- No --> location[Request precise device location]
    location --> submit[Send selected option and verification details with bearer token]
    submit --> server[API derives account ID from verified token]
    server --> validate[Validate poll is open, required fields, age, GPS accuracy, and county match]
    validate --> valid{All checks pass?}
    valid -- No --> error[Return a meaningful validation error; do not record vote]
    valid -- Yes --> reserve[Reserve account, National ID, and voter key for this poll]
    reserve --> unique{All identity claims are unique?}
    unique -- No --> conflict[Return already-voted conflict]
    unique -- Yes --> commit[Commit identity claims, ballot, and updated tally to shared database]
    commit --> success[Return success and receipt]
    success --> ui[Show selected option and VOTED badge; disable options]
```

## 4. Two devices submit at nearly the same time

A client-side status check is helpful for the interface, but it cannot prevent a race by itself. The database's unique claim key is the final guard when simultaneous requests arrive.

```mermaid
sequenceDiagram
    participant Phone
    participant Browser
    participant API as FastAPI API
    participant DB as Shared SQLite database

    Phone->>API: Check account ballot
    API->>DB: No ballot found
    DB-->>API: Not voted
    API-->>Phone: hasVoted = false
    Browser->>API: Check account ballot
    API->>DB: No ballot found
    DB-->>API: Not voted
    API-->>Browser: hasVoted = false
    Phone->>API: Submit ballot with signed-in account
    Browser->>API: Submit ballot with signed-in account
    API->>DB: Insert unique claims and ballot in one transaction
    DB-->>API: First unique claim wins
    API-->>Phone: Success and receipt
    API->>DB: Second insert conflicts on unique identity claim
    DB-->>API: Roll back second transaction
    API-->>Browser: Already-voted conflict
    Browser->>Browser: Lock options and show VOTED badge
    Note over Browser,API: On the next status sync, the web restores the saved option. Android rechecks immediately after a duplicate conflict.
```

Claims are scoped to ballot type and poll ID, then identity type and identity value. Poll submissions reserve the authenticated account ID, National ID, and voter key. A conflict rolls back the second submission, so it does not increment the tally. Android immediately fetches the committed vote after a duplicate conflict; the web locks the poll as VOTED and restores the choice during its next account-status sync.

## 5. What persists where

```mermaid
flowchart LR
    login[Sign-in form] --> auth[Authentication API]
    auth -->|Verify credentials| users[(Users table)]
    auth -->|Return signed bearer token| client[Website local storage<br/>or Android preferences]
    client -->|Authorization: Bearer token| api[Poll API]
    api -->|Verify token; derive account ID| subject[Token subject / account ID]
    subject -->|Write UserId| ballot[(VoteTransactions table)]
    ballot -->|Vote status by account or ID| api
    api -->|hasVoted and optionIndex| client
```

The login token is stored on the client so the user stays signed in. The ballot itself is stored on the server in the shared database and linked to the authenticated account. The app's local voted cache helps restore the interface during an outage; it is not the authoritative record.

## Key behavior

- One account, National ID, or voter key can claim only one ballot per poll.
- A submitted ballot is immutable; refresh, sign-out, another device, or reinstall does not clear the server record.
- A signed-in account with a recorded ballot can recover its selected option and VOTED badge without a locally saved ID.
- First-time voting still requires valid voter details and a precise location that matches the selected county.
- If the API cannot confirm ballot status, the client should not submit until it can check again.
