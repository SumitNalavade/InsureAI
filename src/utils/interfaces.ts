export interface IFile {
    id: string
    url: string
    file: File
}

export interface IConversation {
    text: string
    type: 'question' | 'answer'
}