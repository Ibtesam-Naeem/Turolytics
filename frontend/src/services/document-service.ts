import { apiClient } from '@/lib/api-client';

export type DocumentCategory = 
  | 'gas_receipt'
  | 'parking_ticket'
  | 'toll_booth'
  | 'insurance'
  | 'maintenance'
  | 'repair'
  | 'registration'
  | 'inspection'
  | 'business_expense'
  | 'other';

export interface Document {
  id: number;
  account_id: number;
  vehicle_id?: number;
  file_name: string;
  file_type: string;
  file_size: number;
  s3_key: string;
  s3_bucket: string;
  category: DocumentCategory;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface UploadDocumentRequest {
  category: DocumentCategory;
  vehicle_id?: number;
  description?: string;
  file: File;
}

class DocumentService {
  async uploadDocument(request: UploadDocumentRequest): Promise<Document> {
    const formData = new FormData();
    formData.append('file', request.file);
    formData.append('category', request.category);
    if (request.vehicle_id) {
      formData.append('vehicle_id', request.vehicle_id.toString());
    }
    if (request.description) {
      formData.append('description', request.description);
    }

    const response = await apiClient.post<{ success: boolean; data: { document: Document } }>(
      '/api/s3/upload',
      formData
    );
    return response.data.document;
  }

  async listDocuments(params?: {
    vehicle_id?: number;
    category?: DocumentCategory;
    search?: string;
    limit?: number;
    offset?: number;
  }): Promise<{ documents: Document[]; total: number }> {
    const queryParams = new URLSearchParams();
    if (params?.vehicle_id !== undefined) {
      queryParams.append('vehicle_id', params.vehicle_id.toString());
    }
    if (params?.category) {
      queryParams.append('category', params.category);
    }
    if (params?.search) {
      queryParams.append('search', params.search);
    }
    if (params?.limit) {
      queryParams.append('limit', params.limit.toString());
    }
    if (params?.offset) {
      queryParams.append('offset', params.offset.toString());
    }

    const response = await apiClient.get<{ success: boolean; data: { documents: Document[]; total: number } }>(
      `/api/s3/list?${queryParams.toString()}`
    );
    return response.data;
  }

  async getDocument(documentId: number): Promise<Document> {
    const response = await apiClient.get<{ success: boolean; data: { document: Document } }>(
      `/api/s3/${documentId}`
    );
    return response.data.document;
  }

  async downloadDocument(documentId: number): Promise<Blob> {
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
    
    const response = await fetch(
      `${API_BASE_URL}/api/s3/${documentId}?action=download`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }
    );
    if (!response.ok) {
      throw new Error('Failed to download document');
    }
    return response.blob();
  }

  async deleteDocument(documentId: number): Promise<void> {
    await apiClient.delete(`/api/s3/${documentId}`);
  }

  async getCategories(): Promise<{ value: string; label: string }[]> {
    const response = await apiClient.get<{ success: boolean; data: { categories: { value: string; label: string }[] } }>(
      '/api/s3/categories/list'
    );
    return response.data.categories;
  }
}

export const documentService = new DocumentService();

