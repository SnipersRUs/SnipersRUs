const API_URL = 'http://localhost:3000';

// Helper for API calls
async function apiCall(endpoint: string, options?: RequestInit) {
    const response = await fetch(`${API_URL}${endpoint}`, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options?.headers,
        },
    });

    if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
    }

    return response.json();
}

// Signals API
export const signalsApi = {
    getAll: () => apiCall('/api/signals'),
    getById: (id: string) => apiCall(`/api/signals/${id}`),
    create: (signal: any) => apiCall('/api/signals', {
        method: 'POST',
        body: JSON.stringify(signal),
    }),
    settle: (id: string, outcome: 'HIT' | 'MISS') => apiCall(`/api/signals/${id}/settle`, {
        method: 'POST',
        body: JSON.stringify({ outcome }),
    }),
};

// Bets API
export const betsApi = {
    getByUser: (address: string) => apiCall(`/api/bets/${address}`),
    place: (bet: any) => apiCall('/api/bets', {
        method: 'POST',
        body: JSON.stringify(bet),
    }),
};

// Users API
export const usersApi = {
    getByAddress: (address: string) => apiCall(`/api/users/${address}`),
    getChallenge: () => apiCall('/api/users/auth/challenge', { method: 'POST' }),
    verify: (data: any) => apiCall('/api/users/auth/verify', {
        method: 'POST',
        body: JSON.stringify(data),
    }),
    updateKarma: (address: string, delta: number) => apiCall(`/api/users/${address}/karma`, {
        method: 'POST',
        body: JSON.stringify({ delta }),
    }),
};

// Health check
export const healthCheck = () => apiCall('/health');
