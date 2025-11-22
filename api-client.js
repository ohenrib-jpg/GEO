// static/js/api-client.js - CLIENT API SIMPLIFIÉ
class ApiClient {
    static async request(method, url, data = null) {
        try {
            const options = {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                }
            };
            
            if (data) {
                options.body = JSON.stringify(data);
            }
            
            const response = await fetch(url, options);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`API ${method} Error:`, error);
            throw error;
        }
    }
    
    static async get(url) {
        return this.request('GET', url);
    }
    
    static async post(url, data) {
        return this.request('POST', url, data);
    }
    
    static async put(url, data) {
        return this.request('PUT', url, data);
    }
    
    static async delete(url) {
        return this.request('DELETE', url);
    }
}

// Exposer globalement
window.ApiClient = ApiClient;
console.log("✅ ApiClient chargé");