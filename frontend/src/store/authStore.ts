import { create } from "zustand";

interface AuthStore {
    accessToken: string | null;
    setToken: (token: string) => void;
    clear: () => void;
}

export const useAuthStore = create<AuthStore>((set) => ({
    accessToken: null,
    setToken: (token) => set({ accessToken: token }),
    clear: () => set({ accessToken: null })
}))