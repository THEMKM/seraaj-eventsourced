# TODO / Next Steps (Onboarding + Matching Integration)

This file tracks follow-ups for the newly added onboarding flow and related integration work.

- Profile editing parity
  - Extend Profile page to edit: location, skills, interests/causes, availability (weekdays/weekends/evenings).
  - Wire UI to BFF via SDK (PUT /volunteer/{id}/profile) for these fields.

- Onboarding completion flag
  - Add a backend flag (e.g., `onboardingCompleted`) in Auth profile so the server can decide whether to show onboarding.
  - Gate `/onboarding` to skip if completed; only enforce after registration or if incomplete.

- Validation & UX polish
  - Require at least one cause and (for volunteers) one skill and an availability option.
  - Add inline validation messages and step-level CTA disable logic (partially present, refine copy and i18n where needed).

- Organization onboarding
  - Replace temporary reuse of volunteer profile fields with a proper organization entity and API (create/update org, link admin user).

- Matching data quality
  - Ensure fields stored from onboarding map exactly to matching inputs (skills, availability, location normalization).
  - Consider light geocoding or normalized location enum for better distance scoring.

- Error handling
  - Add UI feedback for network/server errors during onboarding save, with retry.

- Optional enhancements
  - Add a “welcome tips” panel on dashboard after onboarding to encourage quick match.
  - Persist partial onboarding progress (localStorage) to resume if the user navigates away.

