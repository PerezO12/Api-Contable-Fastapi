# Guía para IA: Desarrollo Frontend React + TypeScript - Sistema Contable

## 📋 Contexto del Proyecto

Estás desarrollando el frontend de un **Sistema Contable** con las siguientes características:
- **Backend**: FastAPI con autenticación JWT 
- **Base de datos**: PostgreSQL
- **Sistema de roles**: ADMIN, CONTADOR, SOLO_LECTURA
- **Autenticación**: JWT con access/refresh tokens
- **Documentación API**: Disponible en `/documentation/auth/`

## 🎯 Objetivo Actual: Sistema de Login

Debes crear **ÚNICAMENTE** las funcionalidades relacionadas con autenticación:
- Login/Logout
- Gestión de tokens
- Protección de rutas
- Manejo de roles
- Estados de autenticación

## 🏗️ 1. Arquitectura y Estructura del Proyecto

### Estructura de Carpetas por Dominio
```
src/
├── components/           # Componentes UI reutilizables
│   ├── ui/              # Componentes básicos (Button, Input, etc.)
│   ├── forms/           # Componentes de formularios
│   └── layout/          # Layout y navegación
├── features/            # Características por dominio
│   └── auth/           # 🎯 ENFOQUE PRINCIPAL
│       ├── components/  # Componentes específicos de auth
│       ├── hooks/      # Hooks personalizados de auth
│       ├── services/   # Llamadas API de auth
│       ├── types/      # Tipos TypeScript de auth
│       └── utils/      # Utilidades de auth
├── shared/             # Código compartido
│   ├── api/           # Cliente HTTP y configuración
│   ├── hooks/         # Hooks globales
│   ├── types/         # Tipos globales
│   ├── utils/         # Utilidades globales
│   └── constants/     # Constantes del sistema
├── stores/            # Gestión de estado global
├── styles/            # Estilos globales y temas
└── App.tsx           # Componente raíz
```

### Capas de Arquitectura
1. **Presentación**: Componentes React (UI)
2. **Lógica de Negocio**: Hooks personalizados y Context
3. **Servicios/API**: Comunicación con backend
4. **Estado**: Context/Reducer para estado global

## 🔧 2. Configuración TypeScript

### tsconfig.json
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["DOM", "DOM.Iterable", "ES6"],
    "allowJs": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noFallthroughCasesInSwitch": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@/components/*": ["src/components/*"],
      "@/features/*": ["src/features/*"],
      "@/shared/*": ["src/shared/*"],
      "@/stores/*": ["src/stores/*"]
    }
  },
  "include": [
    "src"
  ],
  "exclude": [
    "node_modules",
    "build",
    "dist"
  ]
}
```

## 🎨 3. Sistema de Diseño y Componentes

### Atomic Design para Auth
```
components/
├── ui/                    # Átomos
│   ├── Button.tsx
│   ├── Input.tsx
│   ├── Label.tsx
│   ├── Card.tsx
│   └── Spinner.tsx
├── forms/                 # Moléculas
│   ├── FormField.tsx
│   ├── PasswordField.tsx
│   └── ValidationMessage.tsx
└── layout/               # Organismos
    ├── AuthLayout.tsx
    ├── Header.tsx
    └── ProtectedRoute.tsx
```

### Componente Ejemplo: Button
```typescript
// src/components/ui/Button.tsx
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  children: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  children,
  disabled,
  ...props
}) => {
  return (
    <button
      disabled={disabled || isLoading}
      className={`btn btn-${variant} btn-${size}`}
      {...props}
    >
      {isLoading ? <Spinner size="sm" /> : children}
    </button>
  );
};
```

## 🔐 4. Feature: Auth - Implementación Completa

### Tipos TypeScript para Auth
```typescript
// src/features/auth/types/index.ts
export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  last_login?: string;
  force_password_change: boolean;
  created_at: string;
}

export enum UserRole {
  ADMIN = 'ADMIN',
  CONTADOR = 'CONTADOR',
  SOLO_LECTURA = 'SOLO_LECTURA'
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token: string;
}

export interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  clearError: () => void;
}
```

### Servicio de Autenticación
```typescript
// src/features/auth/services/authService.ts
import { apiClient } from '@/shared/api/client';
import type { LoginCredentials, AuthTokens, User } from '../types';

export class AuthService {
  private static readonly BASE_URL = '/auth';

  static async login(credentials: LoginCredentials): Promise<AuthTokens> {
    const response = await apiClient.post<AuthTokens>(
      `${this.BASE_URL}/login`,
      credentials
    );
    return response.data;
  }

  static async refreshToken(refresh_token: string): Promise<AuthTokens> {
    const response = await apiClient.post<AuthTokens>(
      `${this.BASE_URL}/refresh`,
      { refresh_token }
    );
    return response.data;
  }

  static async logout(): Promise<void> {
    await apiClient.post(`${this.BASE_URL}/logout`);
  }

  static async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/users/me');
    return response.data;
  }

  static async changePassword(passwordData: {
    current_password: string;
    new_password: string;
    confirm_password: string;
  }): Promise<void> {
    await apiClient.put('/users/me/password', passwordData);
  }
}
```

### Context de Autenticación
```typescript
// src/features/auth/context/AuthContext.tsx
import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { AuthService } from '../services/authService';
import { TokenManager } from '../utils/tokenManager';
import type { AuthState, AuthContextType, LoginCredentials } from '../types';

// Reducer
type AuthAction =
  | { type: 'LOGIN_START' }
  | { type: 'LOGIN_SUCCESS'; payload: { user: User; tokens: AuthTokens } }
  | { type: 'LOGIN_ERROR'; payload: string }
  | { type: 'LOGOUT' }
  | { type: 'SET_USER'; payload: User }
  | { type: 'CLEAR_ERROR' }
  | { type: 'SET_LOADING'; payload: boolean };

const authReducer = (state: AuthState, action: AuthAction): AuthState => {
  switch (action.type) {
    case 'LOGIN_START':
      return { ...state, isLoading: true, error: null };
    
    case 'LOGIN_SUCCESS':
      return {
        ...state,
        user: action.payload.user,
        tokens: action.payload.tokens,
        isAuthenticated: true,
        isLoading: false,
        error: null
      };
    
    case 'LOGIN_ERROR':
      return {
        ...state,
        isLoading: false,
        error: action.payload,
        isAuthenticated: false,
        user: null,
        tokens: null
      };
    
    case 'LOGOUT':
      return {
        ...state,
        user: null,
        tokens: null,
        isAuthenticated: false,
        error: null
      };
    
    case 'SET_USER':
      return { ...state, user: action.payload };
    
    case 'CLEAR_ERROR':
      return { ...state, error: null };
    
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    
    default:
      return state;
  }
};

const initialState: AuthState = {
  user: null,
  tokens: null,
  isAuthenticated: false,
  isLoading: false,
  error: null
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Inicialización: verificar tokens existentes
  useEffect(() => {
    const initAuth = async () => {
      const tokens = TokenManager.getTokens();
      if (tokens && !TokenManager.isTokenExpired(tokens.access_token)) {
        try {
          dispatch({ type: 'SET_LOADING', payload: true });
          const user = await AuthService.getCurrentUser();
          dispatch({ 
            type: 'LOGIN_SUCCESS', 
            payload: { user, tokens } 
          });
        } catch (error) {
          TokenManager.clearTokens();
          dispatch({ type: 'LOGOUT' });
        } finally {
          dispatch({ type: 'SET_LOADING', payload: false });
        }
      }
    };

    initAuth();
  }, []);

  const login = async (credentials: LoginCredentials) => {
    dispatch({ type: 'LOGIN_START' });
    
    try {
      const tokens = await AuthService.login(credentials);
      TokenManager.setTokens(tokens);
      
      const user = await AuthService.getCurrentUser();
      
      dispatch({ 
        type: 'LOGIN_SUCCESS', 
        payload: { user, tokens } 
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      dispatch({ type: 'LOGIN_ERROR', payload: errorMessage });
      throw error;
    }
  };

  const logout = async () => {
    try {
      await AuthService.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      TokenManager.clearTokens();
      dispatch({ type: 'LOGOUT' });
    }
  };

  const refreshToken = async () => {
    const tokens = TokenManager.getTokens();
    if (!tokens?.refresh_token) {
      dispatch({ type: 'LOGOUT' });
      return;
    }

    try {
      const newTokens = await AuthService.refreshToken(tokens.refresh_token);
      TokenManager.setTokens(newTokens);
      dispatch({ 
        type: 'LOGIN_SUCCESS', 
        payload: { user: state.user!, tokens: newTokens } 
      });
    } catch (error) {
      dispatch({ type: 'LOGOUT' });
      TokenManager.clearTokens();
    }
  };

  const clearError = () => {
    dispatch({ type: 'CLEAR_ERROR' });
  };

  const value: AuthContextType = {
    ...state,
    login,
    logout,
    refreshToken,
    clearError
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
```

### Utilidades de Token
```typescript
// src/features/auth/utils/tokenManager.ts
import type { AuthTokens } from '../types';

export class TokenManager {
  private static readonly ACCESS_TOKEN_KEY = 'access_token';
  private static readonly REFRESH_TOKEN_KEY = 'refresh_token';
  private static readonly TOKEN_EXPIRY_KEY = 'token_expiry';

  static setTokens(tokens: AuthTokens): void {
    localStorage.setItem(this.ACCESS_TOKEN_KEY, tokens.access_token);
    localStorage.setItem(this.REFRESH_TOKEN_KEY, tokens.refresh_token);
    
    const expiryTime = Date.now() + (tokens.expires_in * 1000);
    localStorage.setItem(this.TOKEN_EXPIRY_KEY, expiryTime.toString());
  }

  static getTokens(): AuthTokens | null {
    const access_token = localStorage.getItem(this.ACCESS_TOKEN_KEY);
    const refresh_token = localStorage.getItem(this.REFRESH_TOKEN_KEY);
    const expiry = localStorage.getItem(this.TOKEN_EXPIRY_KEY);

    if (!access_token || !refresh_token || !expiry) {
      return null;
    }

    return {
      access_token,
      refresh_token,
      token_type: 'bearer',
      expires_in: Math.max(0, Math.floor((parseInt(expiry) - Date.now()) / 1000))
    };
  }

  static getAccessToken(): string | null {
    return localStorage.getItem(this.ACCESS_TOKEN_KEY);
  }

  static clearTokens(): void {
    localStorage.removeItem(this.ACCESS_TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    localStorage.removeItem(this.TOKEN_EXPIRY_KEY);
  }

  static isTokenExpired(token: string): boolean {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return Date.now() >= payload.exp * 1000;
    } catch {
      return true;
    }
  }

  static shouldRefreshToken(): boolean {
    const expiry = localStorage.getItem(this.TOKEN_EXPIRY_KEY);
    if (!expiry) return false;
    
    // Renovar si expira en menos de 5 minutos
    const expiryTime = parseInt(expiry);
    const fiveMinutesFromNow = Date.now() + (5 * 60 * 1000);
    
    return expiryTime <= fiveMinutesFromNow;
  }
}
```

### Hook personalizado para Auth
```typescript
// src/features/auth/hooks/useAuthGuard.ts
import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import type { UserRole } from '../types';

interface UseAuthGuardOptions {
  requireAuth?: boolean;
  allowedRoles?: UserRole[];
  redirectTo?: string;
}

export const useAuthGuard = ({
  requireAuth = true,
  allowedRoles,
  redirectTo = '/login'
}: UseAuthGuardOptions = {}) => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (isLoading) return;

    // Verificar autenticación
    if (requireAuth && !isAuthenticated) {
      navigate(redirectTo, { 
        state: { from: location.pathname },
        replace: true 
      });
      return;
    }

    // Verificar roles
    if (isAuthenticated && user && allowedRoles && !allowedRoles.includes(user.role)) {
      navigate('/unauthorized', { replace: true });
      return;
    }

    // Verificar cambio de contraseña forzado
    if (isAuthenticated && user?.force_password_change && location.pathname !== '/change-password') {
      navigate('/change-password', { replace: true });
      return;
    }
  }, [isAuthenticated, user, isLoading, navigate, location, requireAuth, allowedRoles, redirectTo]);

  return {
    isAuthorized: isAuthenticated && (!allowedRoles || (user && allowedRoles.includes(user.role))),
    user,
    isLoading
  };
};
```

### Componente de Login
```typescript
// src/features/auth/components/LoginForm.tsx
import React, { useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card } from '@/components/ui/Card';

interface LocationState {
  from?: string;
}

export const LoginForm: React.FC = () => {
  const [credentials, setCredentials] = useState({
    email: '',
    password: ''
  });
  const [showPassword, setShowPassword] = useState(false);

  const { login, isLoading, error, isAuthenticated, clearError } = useAuth();
  const location = useLocation();
  
  const from = (location.state as LocationState)?.from || '/dashboard';

  // Redirigir si ya está autenticado
  if (isAuthenticated) {
    return <Navigate to={from} replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    
    try {
      await login(credentials);
    } catch (error) {
      // Error ya manejado en el context
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setCredentials(prev => ({ ...prev, [name]: value }));
    
    // Limpiar error al escribir
    if (error) clearError();
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md p-8">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900">
            Sistema Contable
          </h1>
          <p className="text-gray-600 mt-2">
            Inicia sesión para continuar
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">
              Email
            </label>
            <Input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              value={credentials.email}
              onChange={handleInputChange}
              placeholder="usuario@empresa.com"
              className="mt-1"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700">
              Contraseña
            </label>
            <div className="mt-1 relative">
              <Input
                id="password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                required
                value={credentials.password}
                onChange={handleInputChange}
                placeholder="••••••••"
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? '🙈' : '👁️'}
              </button>
            </div>
          </div>

          <Button
            type="submit"
            className="w-full"
            isLoading={isLoading}
            disabled={!credentials.email || !credentials.password}
          >
            {isLoading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
          </Button>
        </form>

        <div className="mt-6 text-center text-sm text-gray-500">
          ¿Problemas para acceder? Contacta al administrador
        </div>
      </Card>
    </div>
  );
};
```

### Componente de Ruta Protegida
```typescript
// src/components/layout/ProtectedRoute.tsx
import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/features/auth/context/AuthContext';
import type { UserRole } from '@/features/auth/types';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: UserRole[];
  requireAuth?: boolean;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  allowedRoles,
  requireAuth = true
}) => {
  const { isAuthenticated, user, isLoading } = useAuth();
  const location = useLocation();

  // Mostrar loading mientras verifica autenticación
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Verificar autenticación
  if (requireAuth && !isAuthenticated) {
    return (
      <Navigate 
        to="/login" 
        state={{ from: location.pathname }} 
        replace 
      />
    );
  }

  // Verificar roles permitidos
  if (isAuthenticated && user && allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/unauthorized" replace />;
  }

  // Verificar cambio de contraseña forzado
  if (isAuthenticated && user?.force_password_change && location.pathname !== '/change-password') {
    return <Navigate to="/change-password" replace />;
  }

  return <>{children}</>;
};
```

## 🌐 5. Cliente HTTP con Interceptores

### Configuración de Axios
```typescript
// src/shared/api/client.ts
import axios, { AxiosResponse, AxiosError } from 'axios';
import { TokenManager } from '@/features/auth/utils/tokenManager';

// Configuración base
export const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor de request: agregar token
apiClient.interceptors.request.use(
  (config) => {
    const token = TokenManager.getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Interceptor de response: manejar token expirado
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const tokens = TokenManager.getTokens();
        if (tokens?.refresh_token) {
          const response = await axios.post(
            `${apiClient.defaults.baseURL}/auth/refresh`,
            { refresh_token: tokens.refresh_token }
          );
          
          TokenManager.setTokens(response.data);
          
          // Reintentar request original
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`;
          }
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        TokenManager.clearTokens();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
```

## 🎨 6. Estilos con Tailwind CSS

### tailwind.config.js
```javascript
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
        success: {
          50: '#f0fdf4',
          500: '#22c55e',
          600: '#16a34a',
        },
        danger: {
          50: '#fef2f2',
          500: '#ef4444',
          600: '#dc2626',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}
```

## 🧪 7. Testing Strategy

### Test para Hook de Auth
```typescript
// src/features/auth/__tests__/useAuth.test.tsx
import { renderHook, act } from '@testing-library/react';
import { AuthProvider, useAuth } from '../context/AuthContext';
import { AuthService } from '../services/authService';

// Mock del servicio
jest.mock('../services/authService');
const mockAuthService = AuthService as jest.Mocked<typeof AuthService>;

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <AuthProvider>{children}</AuthProvider>
);

describe('useAuth', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  it('should login successfully', async () => {
    const mockTokens = {
      access_token: 'mock-access-token',
      refresh_token: 'mock-refresh-token',
      token_type: 'bearer',
      expires_in: 1800
    };

    const mockUser = {
      id: '1',
      email: 'test@test.com',
      full_name: 'Test User',
      role: 'ADMIN' as const,
      is_active: true,
      force_password_change: false,
      created_at: '2025-01-01T00:00:00Z'
    };

    mockAuthService.login.mockResolvedValue(mockTokens);
    mockAuthService.getCurrentUser.mockResolvedValue(mockUser);

    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.login({
        email: 'test@test.com',
        password: 'password123'
      });
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user).toEqual(mockUser);
  });

  it('should handle login error', async () => {
    mockAuthService.login.mockRejectedValue(new Error('Invalid credentials'));

    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      try {
        await result.current.login({
          email: 'test@test.com',
          password: 'wrong-password'
        });
      } catch (error) {
        // Expected error
      }
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.error).toBe('Invalid credentials');
  });
});
```

### Test para LoginForm
```typescript
// src/features/auth/components/__tests__/LoginForm.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { LoginForm } from '../LoginForm';

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        {component}
      </AuthProvider>
    </BrowserRouter>
  );
};

describe('LoginForm', () => {
  it('should render login form', () => {
    renderWithProviders(<LoginForm />);
    
    expect(screen.getByText('Sistema Contable')).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/contraseña/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /iniciar sesión/i })).toBeInTheDocument();
  });

  it('should handle form submission', async () => {
    renderWithProviders(<LoginForm />);
    
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/contraseña/i);
    const submitButton = screen.getByRole('button', { name: /iniciar sesión/i });

    fireEvent.change(emailInput, { target: { value: 'test@test.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(submitButton).toHaveTextContent('Iniciando sesión...');
    });
  });
});
```

## 🔒 8. Seguridad Frontend

### Validación de Inputs
```typescript
// src/shared/utils/validation.ts
export const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

export const validatePassword = (password: string): {
  isValid: boolean;
  errors: string[];
} => {
  const errors: string[] = [];
  
  if (password.length < 8) {
    errors.push('La contraseña debe tener al menos 8 caracteres');
  }
  
  if (!/[A-Z]/.test(password)) {
    errors.push('Debe contener al menos una mayúscula');
  }
  
  if (!/[a-z]/.test(password)) {
    errors.push('Debe contener al menos una minúscula');
  }
  
  if (!/\d/.test(password)) {
    errors.push('Debe contener al menos un número');
  }
  
  if (!/[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(password)) {
    errors.push('Debe contener al menos un carácter especial');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
};
```

### Sanitización de Datos
```typescript
// src/shared/utils/sanitization.ts
import DOMPurify from 'dompurify';

export const sanitizeHtml = (dirty: string): string => {
  return DOMPurify.sanitize(dirty);
};

export const sanitizeInput = (input: string): string => {
  return input.trim().replace(/[<>]/g, '');
};
```

## 🚀 9. Configuración del Proyecto

### package.json (dependencias principales)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.8.0",
    "axios": "^1.3.0",
    "dompurify": "^3.0.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^5.16.5",
    "@testing-library/react": "^13.4.0",
    "@testing-library/user-event": "^14.4.3",
    "@types/react": "^18.0.27",
    "@types/react-dom": "^18.0.10",
    "typescript": "^4.9.4",
    "tailwindcss": "^3.2.0",
    "eslint": "^8.34.0",
    "prettier": "^2.8.4"
  }
}
```

### Variables de Entorno
```env
# .env.development
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_APP_NAME=Sistema Contable

# .env.production
REACT_APP_API_URL=https://api.contable.com/api/v1
REACT_APP_APP_NAME=Sistema Contable
```

## 📋 10. Checklist de Implementación

### ✅ Autenticación Básica
- [ ] Configurar proyecto React + TypeScript
- [ ] Implementar cliente HTTP con interceptores
- [ ] Crear tipos TypeScript para Auth
- [ ] Implementar AuthService
- [ ] Crear Context de autenticación con reducer
- [ ] Implementar TokenManager
- [ ] Crear hook useAuth
- [ ] Crear componente LoginForm
- [ ] Implementar ProtectedRoute
- [ ] Configurar rutas de la aplicación

### ✅ Componentes UI
- [ ] Crear componentes básicos (Button, Input, Card)
- [ ] Implementar sistema de estilos con Tailwind
- [ ] Crear layout para autenticación
- [ ] Implementar validación de formularios
- [ ] Agregar estados de loading y error

### ✅ Testing
- [ ] Configurar Jest y Testing Library
- [ ] Tests unitarios para useAuth
- [ ] Tests para LoginForm
- [ ] Tests para TokenManager
- [ ] Tests de integración para flujo completo

### ✅ Seguridad
- [ ] Implementar validación de inputs
- [ ] Configurar sanitización de datos
- [ ] Configurar headers de seguridad
- [ ] Implementar manejo seguro de tokens
- [ ] Validar roles y permisos

## 🎯 Próximos Pasos

Una vez completado el sistema de login, las siguientes características a implementar serían:

1. **Cambio de Contraseña Forzado**
2. **Dashboard según Rol**
3. **Gestión de Perfil de Usuario**
4. **Módulo de Cuentas Contables**
5. **Sistema de Notificaciones**

## 📚 Referencias Útiles

- **Documentación API**: `/documentation/auth/`
- **Patrones de Autenticación**: JWT best practices
- **Testing**: React Testing Library docs
- **TypeScript**: Strict mode guidelines
- **Seguridad**: OWASP Frontend Security

---

## ⚠️ Notas Importantes

1. **ENFOQUE EXCLUSIVO**: Solo implementar funcionalidades de autenticación
2. **TypeScript Estricto**: Usar `strict: true` sin excepciones
3. **Testing Obligatorio**: Cobertura mínima del 80%
4. **Seguridad Primera**: Validar y sanitizar todas las entradas
5. **Accesibilidad**: Usar HTML semántico y ARIA labels
6. **Performance**: Implementar lazy loading y memoización
7. **Error Handling**: Manejar todos los casos de error posibles
8. **Mobile First**: Diseño responsive desde el inicio

Esta guía te proporciona todo lo necesario para implementar un sistema de autenticación robusto, seguro y siguiendo las mejores prácticas de React + TypeScript.
