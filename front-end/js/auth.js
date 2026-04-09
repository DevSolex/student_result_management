// Authentication Management
class AuthManager {
    constructor() {
        this.api = window.api;
        this.currentUser = null;
        this.listeners = [];
    }

    // Add event listener for auth state changes
    addListener(callback) {
        this.listeners.push(callback);
    }

    // Remove event listener
    removeListener(callback) {
        this.listeners = this.listeners.filter(listener => listener !== callback);
    }

    // Notify listeners of auth state change
    notifyListeners(event, data) {
        this.listeners.forEach(callback => callback(event, data));
    }

    // Decode JWT token
    decodeToken(token) {
        try {
            const base64Url = token.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
                return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
            }).join(''));
            return JSON.parse(jsonPayload);
        } catch (error) {
            console.error('Error decoding token:', error);
            return null;
        }
    }

    // Get current user from token
    getCurrentUser() {
        const { accessToken } = this.api.getTokens();
        if (!accessToken) return null;

        const decoded = this.decodeToken(accessToken);
        if (!decoded) return null;

        return {
            id: decoded.user_id || decoded.sub,
            email: decoded.email,
            role: decoded.role,
            name: decoded.name || decoded.sub,
            exp: decoded.exp
        };
    }

    // Check if token is expired
    isTokenExpired() {
        const user = this.getCurrentUser();
        if (!user) return true;

        return user.exp * 1000 < Date.now();
    }

    // Login user
    async login(email, password) {
        try {
            const response = await this.api.post('/auth/login', {
                email,
                password
            });

            // Store tokens
            this.api.storeTokens(response.access_token, response.refresh_token);

            // Get user info
            const user = this.getCurrentUser();
            this.currentUser = user;

            // Notify listeners
            this.notifyListeners('login', user);

            return { success: true, user, response };
        } catch (error) {
            console.error('Login error:', error);
            return { 
                success: false, 
                error: error.message || 'Login failed' 
            };
        }
    }

    // Register student
    async registerStudent(email, password, matricNumber) {
        try {
            const response = await this.api.post('/auth/register/student', {
                email,
                password,
                matric_number: matricNumber
            });

            return { success: true, response };
        } catch (error) {
            console.error('Student registration error:', error);
            return { 
                success: false, 
                error: error.message || 'Registration failed' 
            };
        }
    }

    // Register lecturer
    async registerLecturer(email, password, inviteToken) {
        try {
            const response = await this.api.post('/auth/register/lecturer', {
                email,
                password,
                invite_token: inviteToken
            });

            return { success: true, response };
        } catch (error) {
            console.error('Lecturer registration error:', error);
            return { 
                success: false, 
                error: error.message || 'Registration failed' 
            };
        }
    }

    // Logout user
    logout() {
        // Clear tokens
        this.api.clearTokens();
        
        // Clear current user
        this.currentUser = null;

        // Notify listeners
        this.notifyListeners('logout', null);

        // Redirect to login
        window.location.href = '/front-end/login.html';
    }

    // Check if user is authenticated
    isAuthenticated() {
        const { accessToken } = this.api.getTokens();
        return accessToken && !this.isTokenExpired();
    }

    // Get user role
    getUserRole() {
        const user = this.getCurrentUser();
        return user ? user.role : null;
    }

    // Check if user has specific role
    hasRole(role) {
        return this.getUserRole() === role;
    }

    // Redirect based on user role
    redirectByRole() {
        const role = this.getUserRole();
        
        const redirects = {
            'student': '/front-end/student/dashboard.html',
            'lecturer': '/front-end/lecturer/dashboard.html',
            'admin': '/front-end/admin/dashboard.html'
        };

        const redirectUrl = redirects[role];
        if (redirectUrl) {
            window.location.href = redirectUrl;
        } else {
            // If no valid role, redirect to login
            window.location.href = '/front-end/login.html';
        }
    }

    // Initialize auth state
    init() {
        if (this.isAuthenticated()) {
            this.currentUser = this.getCurrentUser();
            this.notifyListeners('authenticated', this.currentUser);
        } else {
            // Clear invalid tokens
            this.api.clearTokens();
            this.notifyListeners('unauthenticated', null);
        }
    }

    // Change password
    async changePassword(currentPassword, newPassword) {
        try {
            const response = await this.api.post('/auth/change-password', {
                current_password: currentPassword,
                new_password: newPassword
            });

            return { success: true, response };
        } catch (error) {
            console.error('Change password error:', error);
            return { 
                success: false, 
                error: error.message || 'Password change failed' 
            };
        }
    }

    // Request password reset
    async requestPasswordReset(email) {
        try {
            const response = await this.api.post('/auth/forgot-password', {
                email
            });

            return { success: true, response };
        } catch (error) {
            console.error('Password reset request error:', error);
            return { 
                success: false, 
                error: error.message || 'Password reset request failed' 
            };
        }
    }

    // Reset password
    async resetPassword(token, newPassword) {
        try {
            const response = await this.api.post('/auth/reset-password', {
                token,
                new_password: newPassword
            });

            return { success: true, response };
        } catch (error) {
            console.error('Password reset error:', error);
            return { 
                success: false, 
                error: error.message || 'Password reset failed' 
            };
        }
    }
}

// Create global auth instance
const auth = new AuthManager();

// Initialize auth on page load
document.addEventListener('DOMContentLoaded', () => {
    auth.init();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AuthManager, auth };
} else {
    window.AuthManager = AuthManager;
    window.auth = auth;
}
