// API Configuration
// Change this URL to match your backend server port
const API_BASE_URL = 'http://localhost:8000/api/v1';

// API Helper Class
class API {
    constructor() {
        this.baseURL = API_BASE_URL;
        this.refreshTokenPromise = null;
    }

    // Get stored tokens
    getTokens() {
        return {
            accessToken: localStorage.getItem('access_token'),
            refreshToken: localStorage.getItem('refresh_token')
        };
    }

    // Store tokens
    storeTokens(accessToken, refreshToken) {
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
    }

    // Clear tokens
    clearTokens() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
    }

    // Refresh access token
    async refreshAccessToken() {
        // Prevent multiple refresh attempts
        if (this.refreshTokenPromise) {
            return this.refreshTokenPromise;
        }

        this.refreshTokenPromise = (async () => {
            const { refreshToken } = this.getTokens();
            if (!refreshToken) {
                throw new Error('No refresh token available');
            }

            try {
                const response = await fetch(`${this.baseURL}/auth/refresh`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ refresh_token: refreshToken })
                });

                if (!response.ok) {
                    throw new Error('Token refresh failed');
                }

                const data = await response.json();
                this.storeTokens(data.access_token, data.refresh_token);
                return data.access_token;
            } catch (error) {
                this.clearTokens();
                window.location.href = '/front-end/login.html';
                throw error;
            } finally {
                this.refreshTokenPromise = null;
            }
        })();

        return this.refreshTokenPromise;
    }

    // Make API request with automatic token handling
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const { accessToken } = this.getTokens();

        // Set up headers
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        // Add authorization header if token exists
        if (accessToken) {
            headers.Authorization = `Bearer ${accessToken}`;
        }

        // Make initial request
        console.log('Making API request to:', url);
        let response = await fetch(url, {
            ...options,
            headers
        }).catch(error => {
            console.error('Network error:', error);
            throw new Error(`Network error: ${error.message}. Please check if the backend server is running on ${this.baseURL}`);
        });

        // Handle 401 Unauthorized - try to refresh token
        if (response.status === 401 && accessToken) {
            try {
                const newToken = await this.refreshAccessToken();
                headers.Authorization = `Bearer ${newToken}`;
                
                // Retry request with new token
                response = await fetch(url, {
                    ...options,
                    headers
                });
            } catch (refreshError) {
                // Refresh failed, redirect to login
                throw refreshError;
            }
        }

        // Handle other errors
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
        }

        return response.json();
    }

    // Convenience methods
    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async patch(endpoint, data) {
        return this.request(endpoint, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }

    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    // File upload
    async upload(endpoint, file, additionalData = {}) {
        const { accessToken } = this.getTokens();
        const formData = new FormData();
        
        formData.append('file', file);
        
        // Add additional data
        Object.keys(additionalData).forEach(key => {
            formData.append(key, additionalData[key]);
        });

        const headers = {};
        if (accessToken) {
            headers.Authorization = `Bearer ${accessToken}`;
        }

        return fetch(`${this.baseURL}${endpoint}`, {
            method: 'POST',
            headers,
            body: formData
        }).then(response => {
            if (!response.ok) {
                throw new Error(`Upload failed: ${response.statusText}`);
            }
            return response.json();
        });
    }
}

// Create global API instance
const api = new API();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { API, api };
} else {
    window.API = API;
    window.api = api;
}
