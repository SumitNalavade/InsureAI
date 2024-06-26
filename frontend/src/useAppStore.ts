import { create } from "zustand";
import { IFile } from "./utils/interfaces";

interface AppState {
    uploadedFiles: IFile[],
    setUploadedFiles: (uploadedFiles: IFile[]) => void

    selectedFile: IFile | null,
    setSelectedFile: (file: IFile | null) => void
}

const useAppStore = create<AppState>()((set) => ({
    uploadedFiles: [],
    setUploadedFiles: (uploadedFiles) => set({ uploadedFiles }),

    selectedFile: null,
    setSelectedFile: (file) => set({ selectedFile: file })
}));

export default useAppStore