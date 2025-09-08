# Issue #4: Evolve Event Schemas for Rich Volunteer Platform Data Model

## 🎯 **AUTONOMOUS AGENT OBJECTIVE**
You must architect and implement sophisticated event schemas and domain models that capture the full complexity of a volunteer management platform while maintaining event sourcing principles. The system must support volunteers, organizations, opportunities, applications, matching, and analytics with rich metadata, internationalization, and complex relationships.

## 🤖 **AGENT CONTEXT & CONSTRAINTS**
- **Architecture**: Event-sourced system with CQRS pattern, PostgreSQL event store
- **Domain Complexity**: Multi-tenant platform with volunteers, organizations, complex matching
- **Data Requirements**: Multilingual support, audit trails, complex workflows, analytics
- **Performance**: Events must be efficiently queryable and projectable to read models
- **Scale**: Design for 10K+ users, 1M+ events, complex aggregate relationships

## 📂 **EXACT FILE STRUCTURE TO CREATE**
```
contracts/
├── events/
│   ├── user/                      # User domain events
│   │   ├── UserRegistered.yaml
│   │   ├── UserProfileUpdated.yaml
│   │   ├── UserPreferencesSet.yaml
│   │   ├── UserTypeSelected.yaml
│   │   └── UserDeactivated.yaml
│   ├── volunteer/                 # Volunteer-specific events
│   │   ├── VolunteerOnboarded.yaml
│   │   ├── VolunteerSkillsUpdated.yaml
│   │   ├── VolunteerAvailabilityChanged.yaml
│   │   ├── VolunteerRatingUpdated.yaml
│   │   └── VolunteerVerified.yaml
│   ├── organization/              # Organization events
│   │   ├── OrganizationRegistered.yaml
│   │   ├── OrganizationProfileUpdated.yaml
│   │   ├── OrganizationVerified.yaml
│   │   ├── OrganizationSuspended.yaml
│   │   └── OrganizationTeamMemberAdded.yaml
│   ├── opportunity/               # Opportunity lifecycle events
│   │   ├── OpportunityCreated.yaml
│   │   ├── OpportunityUpdated.yaml
│   │   ├── OpportunityPublished.yaml
│   │   ├── OpportunityFilled.yaml
│   │   ├── OpportunityExpired.yaml
│   │   └── OpportunityDeleted.yaml
│   ├── application/               # Application workflow events  
│   │   ├── ApplicationSubmitted.yaml
│   │   ├── ApplicationReviewed.yaml
│   │   ├── ApplicationAccepted.yaml
│   │   ├── ApplicationRejected.yaml
│   │   ├── ApplicationWithdrawn.yaml
│   │   └── ApplicationCompleted.yaml
│   ├── matching/                  # Matching and discovery events
│   │   ├── MatchingRequested.yaml
│   │   ├── MatchesGenerated.yaml
│   │   ├── MatchViewed.yaml
│   │   ├── MatchFeedbackReceived.yaml
│   │   └── MatchingPreferencesUpdated.yaml
│   ├── communication/             # Messaging and notifications
│   │   ├── MessageSent.yaml
│   │   ├── NotificationScheduled.yaml
│   │   ├── NotificationDelivered.yaml
│   │   └── CommunicationPreferencesUpdated.yaml
│   ├── analytics/                 # Analytics and tracking events
│   │   ├── UserActivityLogged.yaml
│   │   ├── SearchPerformed.yaml
│   │   ├── FeatureUsageTracked.yaml
│   │   └── ImpactMeasured.yaml
│   └── system/                    # System-level events
│       ├── EventMigrationCompleted.yaml
│       ├── DataExported.yaml
│       ├── SystemMaintenanceScheduled.yaml
│       └── AuditLogGenerated.yaml
├── aggregates/                    # Aggregate root definitions
│   ├── User.yaml
│   ├── Volunteer.yaml
│   ├── Organization.yaml
│   ├── Opportunity.yaml
│   ├── Application.yaml
│   └── MatchingProfile.yaml
├── commands/                      # Command schemas
│   ├── user/
│   ├── volunteer/
│   ├── organization/
│   ├── opportunity/
│   ├── application/
│   └── matching/
├── projections/                   # Read model schemas
│   ├── UserProfile.yaml
│   ├── OpportunityListing.yaml
│   ├── OrganizationProfile.yaml
│   ├── ApplicationSummary.yaml
│   ├── MatchingRecommendations.yaml
│   └── AnalyticsDashboard.yaml
└── shared/                        # Shared types and utilities
    ├── common-types.yaml
    ├── multilingual.yaml
    ├── location.yaml
    ├── datetime.yaml
    └── metadata.yaml
```

## 🏗️ **CORE EVENT SCHEMA SPECIFICATIONS**

### **Base Event Structure**
```yaml
# contracts/shared/base-event.yaml
BaseEvent:
  type: object
  required:
    - eventId
    - eventType
    - aggregateId
    - aggregateType
    - version
    - timestamp
    - causationId
    - correlationId
  properties:
    eventId:
      type: string
      format: uuid
      description: Unique identifier for this specific event
    eventType:
      type: string
      pattern: "^[A-Z][a-zA-Z]*$"
      description: Type of event (PascalCase)
    aggregateId:
      type: string
      format: uuid
      description: ID of the aggregate root this event belongs to
    aggregateType:
      type: string
      enum: [User, Volunteer, Organization, Opportunity, Application, MatchingProfile]
      description: Type of aggregate root
    version:
      type: integer
      minimum: 1
      description: Version of the aggregate after this event
    timestamp:
      type: string
      format: date-time
      description: When the event occurred (ISO 8601)
    causationId:
      type: string
      format: uuid
      description: ID of the command that caused this event
    correlationId:
      type: string
      format: uuid
      description: ID linking related events in a business process
    metadata:
      $ref: "#/definitions/EventMetadata"
    data:
      type: object
      description: Event-specific data payload

EventMetadata:
  type: object
  properties:
    userId:
      type: string
      format: uuid
      description: User who triggered the event
    sessionId:
      type: string
      description: User session identifier
    ipAddress:
      type: string
      format: ipv4
      description: IP address of the user
    userAgent:
      type: string
      description: Browser/client information
    locale:
      type: string
      pattern: "^[a-z]{2}(-[A-Z]{2})?$"
      description: User's locale (e.g., 'en-US', 'ar-JO')
    timezone:
      type: string
      description: User's timezone
    source:
      type: string
      enum: [web-app, mobile-app, api, system, migration]
      description: Source system that generated the event
    tags:
      type: array
      items:
        type: string
      description: Arbitrary tags for categorization
```

### **User Domain Events**

#### **UserRegistered Event**
```yaml
# contracts/events/user/UserRegistered.yaml
UserRegistered:
  allOf:
    - $ref: "../shared/base-event.yaml#/BaseEvent"
  properties:
    data:
      type: object
      required:
        - email
        - hashedPassword
        - registrationMethod
        - acceptedTermsVersion
      properties:
        email:
          type: string
          format: email
          description: User's email address
        hashedPassword:
          type: string
          description: Bcrypt hashed password
        registrationMethod:
          type: string
          enum: [email, google, facebook, apple, linkedin]
          description: How the user registered
        acceptedTermsVersion:
          type: string
          description: Version of terms and conditions accepted
        referralCode:
          type: string
          description: Referral code used during registration
        initialProfile:
          $ref: "#/definitions/InitialProfile"
        marketingConsent:
          type: boolean
          description: Whether user consented to marketing communications
        language:
          type: string
          pattern: "^[a-z]{2}$"
          default: "en"
          description: User's preferred language

InitialProfile:
  type: object
  properties:
    name:
      type: string
      minLength: 2
      maxLength: 100
      description: User's full name
    dateOfBirth:
      type: string
      format: date
      description: User's date of birth (for age verification)
    phoneNumber:
      type: string
      pattern: "^\\+[1-9]\\d{1,14}$"
      description: User's phone number in E.164 format
    location:
      $ref: "../shared/location.yaml#/Location"
```

#### **UserProfileUpdated Event**
```yaml
# contracts/events/user/UserProfileUpdated.yaml
UserProfileUpdated:
  allOf:
    - $ref: "../shared/base-event.yaml#/BaseEvent"
  properties:
    data:
      type: object
      required:
        - updatedFields
        - previousVersion
      properties:
        updatedFields:
          type: array
          items:
            type: string
          description: List of fields that were updated
        previousVersion:
          type: object
          description: Previous values of updated fields
        newProfile:
          $ref: "#/definitions/ProfileData"
        updateReason:
          type: string
          enum: [user_initiated, admin_update, system_migration, data_correction]
          description: Reason for the profile update

ProfileData:
  type: object
  properties:
    personalInfo:
      $ref: "#/definitions/PersonalInfo"
    contactInfo:
      $ref: "#/definitions/ContactInfo"
    location:
      $ref: "../shared/location.yaml#/Location"
    preferences:
      $ref: "#/definitions/UserPreferences"
    privacy:
      $ref: "#/definitions/PrivacySettings"

PersonalInfo:
  type: object
  properties:
    name:
      $ref: "../shared/multilingual.yaml#/MultilingualText"
    bio:
      $ref: "../shared/multilingual.yaml#/MultilingualText"
    avatar:
      $ref: "#/definitions/Avatar"
    dateOfBirth:
      type: string
      format: date
    gender:
      type: string
      enum: [male, female, non_binary, prefer_not_to_say]

ContactInfo:
  type: object
  properties:
    email:
      type: string
      format: email
    phoneNumber:
      type: string
      pattern: "^\\+[1-9]\\d{1,14}$"
    socialMedia:
      type: object
      properties:
        linkedin:
          type: string
          format: uri
        twitter:
          type: string
        instagram:
          type: string
    website:
      type: string
      format: uri

Avatar:
  type: object
  required:
    - url
    - uploadedAt
  properties:
    url:
      type: string
      format: uri
      description: URL to the avatar image
    thumbnailUrl:
      type: string  
      format: uri
      description: URL to thumbnail version
    uploadedAt:
      type: string
      format: date-time
    fileSize:
      type: integer
      description: File size in bytes
    mimeType:
      type: string
      pattern: "^image\/"
    dimensions:
      type: object
      properties:
        width:
          type: integer
        height:
          type: integer
```

### **Volunteer Domain Events**

#### **VolunteerOnboarded Event**
```yaml
# contracts/events/volunteer/VolunteerOnboarded.yaml
VolunteerOnboarded:
  allOf:
    - $ref: "../shared/base-event.yaml#/BaseEvent"
  properties:
    data:
      type: object
      required:
        - userId
        - onboardingData
        - completedSteps
        - onboardingDuration
      properties:
        userId:
          type: string
          format: uuid
          description: Reference to the User aggregate
        onboardingData:
          $ref: "#/definitions/VolunteerOnboardingData"
        completedSteps:
          type: array
          items:
            type: string
          description: List of completed onboarding steps
        onboardingDuration:
          type: integer
          description: Time spent on onboarding in seconds
        skipReasons:
          type: array
          items:
            type: object
            properties:
              step:
                type: string
              reason:
                type: string
          description: Steps that were skipped and why

VolunteerOnboardingData:
  type: object
  required:
    - motivations
    - availability
    - skills
    - causes
  properties:
    motivations:
      type: array
      items:
        type: string
        enum: [
          personal_growth, skill_development, career_advancement,
          giving_back, meeting_people, religious_duty, civic_duty,
          family_tradition, specific_cause_passion, other
        ]
      description: What motivates the volunteer
    availability:
      $ref: "#/definitions/VolunteerAvailability"
    skills:
      $ref: "#/definitions/SkillSet"
    causes:
      $ref: "#/definitions/CausePreferences"
    experience:
      $ref: "#/definitions/VolunteerExperience"
    preferences:
      $ref: "#/definitions/VolunteerPreferences"

VolunteerAvailability:
  type: object
  required:
    - type
    - hoursPerWeek
  properties:
    type:
      type: string
      enum: [full_time, part_time, weekends, flexible, occasional]
    hoursPerWeek:
      type: integer
      minimum: 1
      maximum: 40
    schedule:
      type: object
      properties:
        monday: { $ref: "#/definitions/DayAvailability" }
        tuesday: { $ref: "#/definitions/DayAvailability" }
        wednesday: { $ref: "#/definitions/DayAvailability" }
        thursday: { $ref: "#/definitions/DayAvailability" }
        friday: { $ref: "#/definitions/DayAvailability" }
        saturday: { $ref: "#/definitions/DayAvailability" }
        sunday: { $ref: "#/definitions/DayAvailability" }
    blackoutDates:
      type: array
      items:
        type: object
        properties:
          start:
            type: string
            format: date
          end:
            type: string
            format: date
          reason:
            type: string

DayAvailability:
  type: object
  properties:
    available:
      type: boolean
    timeSlots:
      type: array
      items:
        type: object
        properties:
          start:
            type: string
            pattern: "^([01]?[0-9]|2[0-3]):[0-5][0-9]$"
          end:
            type: string
            pattern: "^([01]?[0-9]|2[0-3]):[0-5][0-9]$"

SkillSet:
  type: object
  properties:
    technical:
      type: array
      items:
        $ref: "#/definitions/Skill"
    interpersonal:
      type: array
      items:
        $ref: "#/definitions/Skill"
    professional:
      type: array
      items:
        $ref: "#/definitions/Skill"
    specialized:
      type: array
      items:
        $ref: "#/definitions/Skill"

Skill:
  type: object
  required:
    - name
    - level
  properties:
    name:
      type: string
      description: Skill name (standardized taxonomy)
    level:
      type: string
      enum: [beginner, intermediate, advanced, expert]
    yearsOfExperience:
      type: integer
      minimum: 0
    certifications:
      type: array
      items:
        type: object
        properties:
          name:
            type: string
          issuingOrganization:
            type: string
          issueDate:
            type: string
            format: date
          expirationDate:
            type: string
            format: date
          credentialUrl:
            type: string
            format: uri
```

### **Opportunity Domain Events**

#### **OpportunityCreated Event**
```yaml
# contracts/events/opportunity/OpportunityCreated.yaml
OpportunityCreated:
  allOf:
    - $ref: "../shared/base-event.yaml#/BaseEvent"
  properties:
    data:
      type: object
      required:
        - organizationId
        - title
        - description
        - requirements
        - commitment
        - location
        - causes
      properties:
        organizationId:
          type: string
          format: uuid
          description: Reference to the Organization aggregate
        createdBy:
          type: string
          format: uuid
          description: User ID who created the opportunity
        title:
          $ref: "../shared/multilingual.yaml#/MultilingualText"
        description:
          $ref: "../shared/multilingual.yaml#/MultilingualText"
        shortDescription:
          $ref: "../shared/multilingual.yaml#/MultilingualText"
        requirements:
          $ref: "#/definitions/OpportunityRequirements"
        commitment:
          $ref: "#/definitions/TimeCommitment"
        location:
          $ref: "#/definitions/OpportunityLocation"
        causes:
          type: array
          items:
            type: string
          minItems: 1
          description: Primary causes this opportunity addresses
        skills:
          $ref: "#/definitions/RequiredSkills"
        benefits:
          $ref: "#/definitions/OpportunityBenefits"
        media:
          $ref: "#/definitions/OpportunityMedia"
        applicationProcess:
          $ref: "#/definitions/ApplicationProcess"
        scheduling:
          $ref: "#/definitions/OpportunityScheduling"
        capacity:
          $ref: "#/definitions/VolunteerCapacity"

OpportunityRequirements:
  type: object
  properties:
    minimumAge:
      type: integer
      minimum: 13
      maximum: 100
    maximumAge:
      type: integer  
      minimum: 13
      maximum: 100
    backgroundCheck:
      type: boolean
      default: false
    references:
      type: boolean
      default: false
    interview:
      type: boolean
      default: false
    orientation:
      type: boolean
      default: false
    training:
      $ref: "#/definitions/TrainingRequirements"
    physicalRequirements:
      type: array
      items:
        type: string
        enum: [
          lifting_heavy_objects, standing_long_periods, walking_distances,
          climbing_stairs, outdoor_work, indoor_work, computer_work,
          driving_required, manual_dexterity, good_vision, good_hearing
        ]
    languages:
      type: array
      items:
        type: object
        properties:
          language:
            type: string
            pattern: "^[a-z]{2}$"
          proficiency:
            type: string
            enum: [basic, conversational, fluent, native]
          required:
            type: boolean

TimeCommitment:
  type: object
  required:
    - type
    - hoursPerWeek
  properties:
    type:
      type: string
      enum: [one_time, short_term, long_term, ongoing, flexible]
    hoursPerWeek:
      type: integer
      minimum: 1
    duration:
      type: object
      properties:
        weeks:
          type: integer
          minimum: 1
        months:
          type: integer
          minimum: 1
        flexible:
          type: boolean
    schedule:
      type: object
      properties:
        fixed:
          type: boolean
        preferredDays:
          type: array
          items:
            type: string
            enum: [monday, tuesday, wednesday, thursday, friday, saturday, sunday]
        preferredTimes:
          type: array
          items:
            type: string
            enum: [early_morning, morning, afternoon, evening, night, flexible]

OpportunityLocation:
  type: object
  required:
    - type
  properties:
    type:
      type: string
      enum: [on_site, remote, hybrid]
    address:
      $ref: "../shared/location.yaml#/DetailedAddress"
    remoteDetails:
      type: object
      properties:
        platformsUsed:
          type: array
          items:
            type: string
        equipmentProvided:
          type: boolean
        internetRequirements:
          type: string
    travelRequirements:
      type: object
      properties:
        required:
          type: boolean
        reimbursed:
          type: boolean
        ownTransportation:
          type: boolean
        maxDistance:
          type: integer
          description: Maximum travel distance in kilometers

RequiredSkills:
  type: object
  properties:
    essential:
      type: array
      items:
        $ref: "#/definitions/SkillRequirement"
      description: Skills that are absolutely required
    preferred:
      type: array
      items:
        $ref: "#/definitions/SkillRequirement"
      description: Skills that would be helpful but not required
    learnable:
      type: array
      items:
        $ref: "#/definitions/SkillRequirement"
      description: Skills that will be taught during the opportunity

SkillRequirement:
  type: object
  required:
    - skill
    - level
  properties:
    skill:
      type: string
      description: Skill name from standardized taxonomy
    level:
      type: string
      enum: [any, beginner, intermediate, advanced, expert]
    weight:
      type: number
      minimum: 0
      maximum: 1
      description: Importance weight for matching algorithm
    alternatives:
      type: array
      items:
        type: string
      description: Alternative skills that could substitute
```

### **Application Workflow Events**

#### **ApplicationSubmitted Event**
```yaml
# contracts/events/application/ApplicationSubmitted.yaml
ApplicationSubmitted:
  allOf:
    - $ref: "../shared/base-event.yaml#/BaseEvent"
  properties:
    data:
      type: object
      required:
        - volunteerId
        - opportunityId
        - applicationData
        - submissionMethod
      properties:
        volunteerId:
          type: string
          format: uuid
          description: Reference to the Volunteer aggregate
        opportunityId:
          type: string
          format: uuid
          description: Reference to the Opportunity aggregate
        submissionMethod:
          type: string
          enum: [web_form, mobile_app, email, phone, in_person]
        applicationData:
          $ref: "#/definitions/ApplicationSubmissionData"
        attachments:
          type: array
          items:
            $ref: "#/definitions/ApplicationAttachment"
        matchingScore:
          type: number
          minimum: 0
          maximum: 1
          description: Computed compatibility score at time of application

ApplicationSubmissionData:
  type: object
  required:
    - personalStatement
    - questionResponses
  properties:
    personalStatement:
      $ref: "../shared/multilingual.yaml#/MultilingualText"
    questionResponses:
      type: array
      items:
        $ref: "#/definitions/QuestionResponse"
    availability:
      $ref: "#/definitions/ApplicationAvailability"
    relevantExperience:
      type: array
      items:
        $ref: "#/definitions/ExperienceEntry"
    references:
      type: array
      items:
        $ref: "#/definitions/Reference"
    accommodations:
      type: string
      description: Any accommodations needed
    emergencyContact:
      $ref: "#/definitions/EmergencyContact"

QuestionResponse:
  type: object
  required:
    - questionId
    - response
  properties:
    questionId:
      type: string
      description: ID of the application question
    questionText:
      type: string
      description: The actual question asked
    questionType:
      type: string
      enum: [text, multiple_choice, rating, boolean, file_upload]
    response:
      oneOf:
        - type: string
        - type: number
        - type: boolean
        - type: array
    metadata:
      type: object
      properties:
        timeSpent:
          type: integer
          description: Seconds spent on this question
        revisionCount:
          type: integer
          description: Number of times the answer was changed

ApplicationAttachment:
  type: object
  required:
    - type
    - url
    - uploadedAt
  properties:
    type:
      type: string
      enum: [resume, cover_letter, portfolio, certificate, reference_letter, other]
    filename:
      type: string
    url:
      type: string
      format: uri
    fileSize:
      type: integer
    mimeType:
      type: string
    uploadedAt:
      type: string
      format: date-time
    description:
      type: string
```

## 🔄 **AGGREGATE ROOT DEFINITIONS**

### **User Aggregate**
```yaml
# contracts/aggregates/User.yaml
User:
  type: object
  description: Core user aggregate containing authentication and basic profile
  required:
    - id
    - email
    - status
    - createdAt
  properties:
    id:
      type: string
      format: uuid
    email:
      type: string
      format: email
    status:
      type: string
      enum: [active, suspended, deactivated, pending_verification]
    profile:
      $ref: "#/definitions/UserProfile"
    authentication:
      $ref: "#/definitions/AuthenticationInfo"
    permissions:
      $ref: "#/definitions/UserPermissions"
    auditTrail:
      $ref: "#/definitions/AuditTrail"
    createdAt:
      type: string
      format: date-time
    updatedAt:
      type: string
      format: date-time
    version:
      type: integer
      minimum: 1

UserProfile:
  type: object
  properties:
    personalInfo:
      $ref: "../events/user/UserProfileUpdated.yaml#/PersonalInfo"
    contactInfo:
      $ref: "../events/user/UserProfileUpdated.yaml#/ContactInfo"
    location:
      $ref: "../shared/location.yaml#/Location"
    preferences:
      $ref: "#/definitions/UserPreferences"
    privacy:
      $ref: "#/definitions/PrivacySettings"
    completionStatus:
      $ref: "#/definitions/ProfileCompletionStatus"

UserPreferences:
  type: object
  properties:
    language:
      type: string
      pattern: "^[a-z]{2}$"
      default: "en"
    timezone:
      type: string
      default: "UTC"
    dateFormat:
      type: string
      enum: [ISO, US, EU]
      default: "ISO"
    theme:
      type: string
      enum: [light, dark, system]
      default: "system"
    notifications:
      $ref: "#/definitions/NotificationPreferences"
    communication:
      $ref: "#/definitions/CommunicationPreferences"

PrivacySettings:
  type: object
  properties:
    profileVisibility:
      type: string
      enum: [public, members_only, private]
      default: "members_only"
    showEmail:
      type: boolean
      default: false
    showPhone:
      type: boolean
      default: false
    showLocation:
      type: boolean
      default: true
    dataSharing:
      $ref: "#/definitions/DataSharingSettings"
    searchable:
      type: boolean
      default: true
      description: Whether profile appears in searches

ProfileCompletionStatus:
  type: object
  properties:
    overallCompletion:
      type: number
      minimum: 0
      maximum: 1
    sections:
      type: object
      properties:
        basicInfo:
          type: boolean
        contactInfo:
          type: boolean
        location:
          type: boolean
        skills:
          type: boolean
        interests:
          type: boolean
        availability:
          type: boolean
    lastUpdated:
      type: string
      format: date-time
```

## 📊 **PROJECTION SCHEMAS**

### **OpportunityListing Projection**
```yaml
# contracts/projections/OpportunityListing.yaml
OpportunityListing:
  type: object
  description: Read model for opportunity search and display
  required:
    - id
    - title
    - organization
    - status
    - createdAt
  properties:
    id:
      type: string
      format: uuid
    title:
      $ref: "../shared/multilingual.yaml#/MultilingualText"
    shortDescription:
      $ref: "../shared/multilingual.yaml#/MultilingualText"
    organization:
      $ref: "#/definitions/OrganizationSummary"
    status:
      type: string
      enum: [draft, active, paused, filled, expired, cancelled]
    urgency:
      type: string
      enum: [low, medium, high, critical]
    featured:
      type: boolean
    verified:
      type: boolean
    location:
      $ref: "#/definitions/LocationSummary"
    commitment:
      $ref: "#/definitions/CommitmentSummary"
    causes:
      type: array
      items:
        type: object
        properties:
          id:
            type: string
          name:
            type: string
          color:
            type: string
    skills:
      $ref: "#/definitions/SkillsSummary"
    capacity:
      $ref: "#/definitions/CapacitySummary"
    dates:
      $ref: "#/definitions/ImportantDates"
    media:
      $ref: "#/definitions/MediaSummary"
    statistics:
      $ref: "#/definitions/OpportunityStatistics"
    searchMetadata:
      $ref: "#/definitions/SearchMetadata"
    createdAt:
      type: string
      format: date-time
    updatedAt:
      type: string
      format: date-time

OrganizationSummary:
  type: object
  properties:
    id:
      type: string
      format: uuid
    name:
      type: string
    logo:
      type: string
      format: uri
    type:
      type: string
    size:
      type: string
    verified:
      type: boolean
    rating:
      type: number
      minimum: 0
      maximum: 5
    location:
      type: string

LocationSummary:
  type: object
  properties:
    type:
      type: string
      enum: [on_site, remote, hybrid]
    city:
      type: string
    country:
      type: string
    coordinates:
      type: object
      properties:
        lat:
          type: number
        lng:
          type: number
    remote:
      type: boolean

CommitmentSummary:
  type: object
  properties:
    type:
      type: string
    hoursPerWeek:
      type: integer
    duration:
      type: string
    schedule:
      type: string
    flexibility:
      type: string
      enum: [rigid, somewhat_flexible, very_flexible]

SearchMetadata:
  type: object
  description: Metadata for search and matching optimization
  properties:
    keywords:
      type: array
      items:
        type: string
      description: Extracted keywords for full-text search
    tags:
      type: array
      items:
        type: string
      description: Categorization tags
    searchWeight:
      type: number
      description: Boost factor for search ranking
    matchingVector:
      type: array
      items:
        type: number
      description: Vector representation for similarity matching
    lastIndexed:
      type: string
      format: date-time
```

## 🔧 **SHARED TYPE DEFINITIONS**

### **Multilingual Support**
```yaml
# contracts/shared/multilingual.yaml
MultilingualText:
  type: object
  description: Text content supporting multiple languages
  required:
    - default
  properties:
    default:
      type: string
      description: Default language text (usually English)
    translations:
      type: object
      patternProperties:
        "^[a-z]{2}(-[A-Z]{2})?$":
          type: string
      description: Translations keyed by locale (e.g., 'ar', 'ar-JO')
    metadata:
      $ref: "#/definitions/TextMetadata"

TextMetadata:
  type: object
  properties:
    autoTranslated:
      type: object
      patternProperties:
        "^[a-z]{2}(-[A-Z]{2})?$":
          type: boolean
      description: Whether translation was automatically generated
    translatedAt:
      type: object
      patternProperties:
        "^[a-z]{2}(-[A-Z]{2})?$":
          type: string
          format: date-time
      description: When translation was created/updated
    translator:
      type: object
      patternProperties:
        "^[a-z]{2}(-[A-Z]{2})?$":
          type: string
      description: Who or what created the translation
```

### **Location Types**
```yaml
# contracts/shared/location.yaml
Location:
  type: object
  required:
    - country
  properties:
    country:
      type: string
      pattern: "^[A-Z]{2}$"
      description: ISO 3166-1 alpha-2 country code
    region:
      type: string
      description: State, province, or region
    city:
      type: string
      description: City or locality
    district:
      type: string
      description: District or neighborhood
    coordinates:
      $ref: "#/definitions/Coordinates"
    timezone:
      type: string
      description: IANA timezone identifier
    metadata:
      $ref: "#/definitions/LocationMetadata"

DetailedAddress:
  allOf:
    - $ref: "#/Location"
  properties:
    streetAddress:
      type: string
      description: Street address line 1
    streetAddress2:
      type: string
      description: Street address line 2
    postalCode:
      type: string
      description: Postal/ZIP code
    landmark:
      type: string
      description: Nearby landmark for reference

Coordinates:
  type: object
  required:
    - latitude
    - longitude
  properties:
    latitude:
      type: number
      minimum: -90
      maximum: 90
    longitude:
      type: number
      minimum: -180
      maximum: 180
    accuracy:
      type: number
      description: Accuracy in meters
    source:
      type: string
      enum: [gps, geocoded, user_entered, estimated]

LocationMetadata:
  type: object
  properties:
    population:
      type: integer
    economicLevel:
      type: string
      enum: [low, lower_middle, upper_middle, high]
    urbanRural:
      type: string
      enum: [urban, suburban, rural]
    safetyRating:
      type: integer
      minimum: 1
      maximum: 5
    accessibilityRating:
      type: integer
      minimum: 1
      maximum: 5
```

## 🎯 **SUCCESS CRITERIA & VALIDATION**

### **Schema Quality Requirements**
- [ ] All events include complete metadata for audit trails
- [ ] Multilingual support implemented for user-facing content
- [ ] Location data supports global operations with proper geocoding
- [ ] Complex relationships properly modeled with aggregate references
- [ ] Event versioning strategy allows for schema evolution
- [ ] Performance considerations built into projection designs
- [ ] Validation rules prevent invalid data at schema level
- [ ] Comprehensive type definitions with proper constraints

### **Business Logic Requirements**  
- [ ] User registration to active volunteer workflow supported
- [ ] Organization verification and opportunity lifecycle captured
- [ ] Application process from submission to completion tracked
- [ ] Matching algorithm integration with rich profile data
- [ ] Analytics and reporting needs addressed in projections
- [ ] Communication and notification events properly structured

### **Technical Requirements**
- [ ] All schemas valid OpenAPI 3.0/JSON Schema format
- [ ] Code generation works for all languages (TypeScript, Python, etc.)
- [ ] Event store queries efficient with proper indexing hints
- [ ] Projection rebuilding supported from event streams
- [ ] Cross-aggregate relationships properly handled
- [ ] Migration path from existing simple schemas

### **Operational Requirements**
- [ ] Event schemas support blue-green deployments
- [ ] Backward compatibility maintained for API consumers  
- [ ] Monitoring and alerting hooks included in event metadata
- [ ] GDPR compliance supported with data classification
- [ ] Event replay and debugging information preserved
- [ ] Performance benchmarks met for event processing

## 🚀 **IMPLEMENTATION GUIDANCE**

### **Development Approach**
1. **Phase 1**: Core domain events (User, Volunteer, Organization)
2. **Phase 2**: Workflow events (Opportunity, Application lifecycle)  
3. **Phase 3**: Advanced features (Matching, Analytics, Communication)
4. **Phase 4**: Optimization and performance tuning

### **Migration Strategy**
- **Gradual Migration**: Migrate one aggregate at a time
- **Event Transformation**: Convert existing simple events to rich schemas
- **Projection Rebuilding**: Regenerate read models from new event structure
- **API Versioning**: Maintain backward compatibility during transition

### **Testing Strategy**
- **Schema Validation**: Automated tests for all schema constraints
- **Event Processing**: Integration tests for event handlers
- **Projection Building**: Tests for read model generation
- **Performance**: Load testing with realistic event volumes

**This sophisticated event schema evolution will transform the platform from basic event sourcing to a rich, scalable, and internationally-ready volunteer management system. Implement with careful attention to data integrity, performance, and maintainability.**