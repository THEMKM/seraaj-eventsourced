/**
 * Generated TypeScript types from contracts/v1.1.0/entities
 * Generated at: 2025-08-11T07:37:00.000Z
 * Source: user.schema.json
 */

/**
 * User role determining access permissions
 */
export enum UserRole {
    VOLUNTEER = "VOLUNTEER",
    ORG_ADMIN = "ORG_ADMIN", 
    SUPERADMIN = "SUPERADMIN"
}

/**
 * A user account in the Seraaj platform with authentication capabilities
 */
export interface User {
    /**
     * Unique user identifier (UUID format)
     */
    id: string;
    
    /**
     * User's email address (used for authentication)
     */
    email: string;
    
    /**
     * User's full name
     */
    name: string;
    
    /**
     * User's role determining access permissions
     */
    role: UserRole;
    
    /**
     * Whether the user's email has been verified
     */
    isVerified: boolean;
    
    /**
     * When the user account was created
     */
    createdAt: string;
    
    /**
     * When the user account was last updated
     */
    updatedAt?: string;
    
    /**
     * When the user last logged in
     */
    lastLoginAt?: string;
    
    /**
     * URL to user's profile image
     */
    profileImageUrl?: string;
}

/**
 * Auth tokens returned from login/register/refresh endpoints
 */
export interface AuthTokens {
    /**
     * JWT access token for API authentication
     */
    accessToken: string;
    
    /**
     * Refresh token for obtaining new access tokens
     */
    refreshToken: string;
    
    /**
     * Access token expiration time in seconds
     */
    expiresIn: number;
    
    /**
     * Token type (always Bearer)
     */
    tokenType: "Bearer";
}

/**
 * Registration request payload
 */
export interface RegisterUserRequest {
    email: string;
    password: string;
    name: string;
    role: UserRole.VOLUNTEER | UserRole.ORG_ADMIN;
}

/**
 * Login request payload
 */
export interface LoginUserRequest {
    email: string;
    password: string;
}

/**
 * Refresh token request payload
 */
export interface RefreshTokenRequest {
    refreshToken: string;
}

/**
 * Registration/Login response
 */
export interface AuthResponse {
    user: User;
    tokens: AuthTokens;
}

/**
 * API Error response
 */
export interface ApiError {
    error: string;
    message: string;
    details?: Record<string, any>;
}