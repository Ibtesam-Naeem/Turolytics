// Stub service for demo mode
export interface DocumentCategory {
  id: string;
  name: string;
}

class DocumentService {
  async getDocuments(params?: any): Promise<{ documents: any[]; total: number }> {
    return { documents: [], total: 0 };
  }

  async uploadDocument(data: any): Promise<any> {
    throw new Error("Document upload not available in demo mode");
  }
}

export const documentService = new DocumentService();
