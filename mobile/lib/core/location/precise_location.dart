import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';

enum PreciseLocationIssue {
  serviceDisabled,
  permissionDenied,
  permissionDeniedForever,
  locationUnavailable,
  insufficientAccuracy,
}

class PreciseLocationAttempt {
  final Position? position;
  final PreciseLocationIssue? issue;

  const PreciseLocationAttempt._({this.position, this.issue});

  bool get succeeded => position != null && issue == null;

  factory PreciseLocationAttempt.success(Position position) =>
      PreciseLocationAttempt._(position: position);

  factory PreciseLocationAttempt.failure(PreciseLocationIssue issue) =>
      PreciseLocationAttempt._(issue: issue);
}

class PreciseLocation {
  static const double maximumAcceptedAccuracyMeters = 500;

  static Future<PreciseLocationAttempt> acquire() async {
    try {
      var permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
      }
      if (permission == LocationPermission.deniedForever) {
        return PreciseLocationAttempt.failure(
          PreciseLocationIssue.permissionDeniedForever,
        );
      }
      if (permission == LocationPermission.denied) {
        return PreciseLocationAttempt.failure(
          PreciseLocationIssue.permissionDenied,
        );
      }

      // Request app access even when Android's location switch is off, then
      // direct the user to Location Settings after permission is resolved.
      if (!await Geolocator.isLocationServiceEnabled()) {
        return PreciseLocationAttempt.failure(
          PreciseLocationIssue.serviceDisabled,
        );
      }

      final position = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.high,
          timeLimit: Duration(seconds: 20),
        ),
      );
      if (!position.accuracy.isFinite ||
          position.accuracy <= 0 ||
          position.accuracy > maximumAcceptedAccuracyMeters) {
        return PreciseLocationAttempt.failure(
          PreciseLocationIssue.insufficientAccuracy,
        );
      }
      return PreciseLocationAttempt.success(position);
    } catch (_) {
      return PreciseLocationAttempt.failure(
        PreciseLocationIssue.locationUnavailable,
      );
    }
  }

  static Future<void> promptSettings(
    BuildContext context,
    PreciseLocationIssue issue,
  ) async {
    final serviceOff = issue == PreciseLocationIssue.serviceDisabled;
    final permissionBlocked = issue == PreciseLocationIssue.permissionDenied ||
        issue == PreciseLocationIssue.permissionDeniedForever;
    final title = serviceOff
        ? 'Turn on device location'
        : permissionBlocked
            ? 'Allow location access'
            : 'Location is unavailable';
    final message = serviceOff
        ? 'Turn on Location Services to verify that your device is in the county you selected. Return here and submit again.'
        : permissionBlocked
            ? 'Allow this app to access your location in Android settings. Return here and submit again.'
            : issue == PreciseLocationIssue.insufficientAccuracy
                ? 'Move to an area with a clearer GPS signal, turn on precise location, and try again.'
                : 'Check that Location Services are on and this app is allowed to access location, then try again.';
    final openSettings = serviceOff || issue == PreciseLocationIssue.locationUnavailable;

    final shouldOpenSettings = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        backgroundColor: const Color(0xFF424242),
        title: Text(title, style: const TextStyle(color: Colors.white)),
        content: Text(message, style: const TextStyle(color: Color(0xFFD0D0D0))),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: const Text('Cancel', style: TextStyle(color: Color(0xFFD0D0D0))),
          ),
          ElevatedButton(
            onPressed: () => Navigator.of(dialogContext).pop(true),
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFFE5E5E5),
              foregroundColor: const Color(0xFF2A2A2A),
            ),
            child: Text(openSettings
                ? 'Open Location Settings'
                : 'Open App Settings'),
          ),
        ],
      ),
    );

    if (shouldOpenSettings != true || !context.mounted) return;
    if (openSettings) {
      await Geolocator.openLocationSettings();
    } else {
      await Geolocator.openAppSettings();
    }
  }
}
