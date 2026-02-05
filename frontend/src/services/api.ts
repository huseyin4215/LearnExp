const API_BASE_URL = 'http://127.0.0.1:8000/api';

interface ApiResponse<T = unknown> {
  success: boolean;
  message: string;
  user?: T;
}

interface User {
  id: number;
  email: string;
  fullName: string;
  isStaff?: boolean;
}

interface LoginData {
  email: string;
  password: string;
}

interface RegisterData {
  fullName: string;
  email: string;
  password: string;
}

export const authApi = {
  async login(data: LoginData): Promise<ApiResponse<User>> {
    const response = await fetch(`${API_BASE_URL}/auth/login/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    return response.json();
  },

  async register(data: RegisterData): Promise<ApiResponse<User>> {
    const response = await fetch(`${API_BASE_URL}/auth/register/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    return response.json();
  },

  async getUser(userId: number): Promise<ApiResponse<User>> {
    const response = await fetch(`${API_BASE_URL}/user/${userId}/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    return response.json();
  },
};

// Kullanıcı bilgilerini localStorage'da sakla
export const userStorage = {
  setUser(user: User) {
    localStorage.setItem('user', JSON.stringify(user));
  },

  getUser(): User | null {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  },

  removeUser() {
    localStorage.removeItem('user');
  },

  isLoggedIn(): boolean {
    return !!this.getUser();
  },
};

