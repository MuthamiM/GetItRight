import 'package:flutter/material.dart';

class AppColors {
  // Official IcapsQ Graphite Spec
  static const Color graphite900 = Color(0xFF1F2023); // Darkest surfaces
  static const Color graphite700 = Color(0xFF2E3035); // Brand primary
  static const Color graphite500 = Color(0xFF6B6E76); // Q on light, tagline
  static const Color graphite300 = Color(0xFFB8BAC0); // Q on dark, borders
  static const Color graphite50 = Color(0xFFF2F2F3); // Light surfaces
  static const Color white = Color(0xFFFFFFFF);

  static const Color bgPrimary = graphite900;
  static const Color bgCard = graphite700;
  static const Color bgElevated = Color(0xFF383A40);
  static const Color accent = graphite50;
  static const Color accentGlow = Color(0x33B8BAC0);
  static const Color textPrimary = Color(0xFFFFFFFF);
  static const Color textSecondary = graphite300;
  static const Color textMuted = graphite500;
  static const Color border = Color(0xFF42454C);
  static const Color error = Color(0xFFFF6B6B);
  static const Color warning = graphite300;
  static const Color success = graphite50;

  // Shared charcoal palette used by the poll and survey feeds.
  static const Color feedBackground = Color(0xFF303030);
  static const Color feedCard = Color(0xFF262626);
  static const Color feedCardBorder = Color(0xFF3E3E3E);
  static const Color feedControl = Color(0xFF404040);
  static const Color feedControlBorder = Color(0xFF606060);
  static const Color feedText = Color(0xFFE5E5E5);
  static const Color feedMuted = Color(0xFFB8B8B8);
  static const Color feedHint = Color(0xFF888888);
}

class AppRadius {
  static const double card = 16.0;
  static const double button = 26.0;
  static const double pill = 26.0;
  static const double small = 8.0;
}

class AppTheme {
  static ThemeData get darkTheme {
    return ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: AppColors.bgPrimary,
      primaryColor: AppColors.accent,
      colorScheme: const ColorScheme.dark(
        primary: AppColors.accent,
        secondary: AppColors.bgElevated,
        surface: AppColors.bgCard,
        error: AppColors.error,
        onPrimary: Colors.black,
        onSecondary: AppColors.textPrimary,
        onSurface: AppColors.textPrimary,
        onError: Colors.white,
      ),
      cardTheme: CardTheme(
        color: AppColors.bgCard,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadius.card),
          side: const BorderSide(color: AppColors.border, width: 1),
        ),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: AppColors.bgPrimary,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: TextStyle(
          color: AppColors.textPrimary,
          fontSize: 18,
          fontWeight: FontWeight.bold,
        ),
        iconTheme: IconThemeData(color: AppColors.textPrimary),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.accent,
          foregroundColor: Colors.black,
          elevation: 0,
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppRadius.pill),
          ),
          textStyle: const TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.textPrimary,
          side: const BorderSide(color: AppColors.border),
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppRadius.button),
          ),
        ),
      ),
      inputDecorationTheme: const InputDecorationTheme(
        filled: false,
        fillColor: Colors.transparent,
        contentPadding: EdgeInsets.symmetric(horizontal: 24, vertical: 16),
        border: InputBorder.none,
        enabledBorder: InputBorder.none,
        focusedBorder: InputBorder.none,
        hintStyle: TextStyle(color: AppColors.textSecondary, fontSize: 15),
      ),
    );
  }
}
