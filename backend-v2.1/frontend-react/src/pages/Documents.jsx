import React, { useState, useEffect, useCallback } from 'react';
import { FileText, Upload, Trash2, Download, Search, File, Image, FileSpreadsheet } from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Documents() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const token = localStorage.getItem('token');
  const axiosConfig = { headers: { Authorization: `Bearer ${token}` } };

  const onDrop = useCallback(async (acceptedFiles) => {
    for (const file of acceptedFiles) {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', file.name);
      try {
        await axios.post(`${API_URL}/api/v1/documents/upload`, formData, {
          headers: { ...axiosConfig.headers, 'Content-Type': 'multipart/form-data' }
        });
      } catch (e) { console.error(e); }
    }
    fetchDocuments();
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/*': [], 'image/*': [], 'text/*': [] }
  });

  const fetchDocuments = async () => {
    try {
      const res = await axios.get(`${API_URL}/api/v1/documents/documents`, axiosConfig);
      setDocuments(res.data);
    } catch (e) { console.error(e); }
  };

  useEffect(() => { fetchDocuments(); }, []);

  const deleteDoc = async (id) => {
    if (!confirm('Delete this document?')) return;
    try {
      await axios.delete(`${API_URL}/api/v1/documents/documents/${id}`, axiosConfig);
      fetchDocuments();
    } catch (e) { console.error(e); }
  };

  const getFileIcon = (mimeType) => {
    if (mimeType?.includes('image')) return <Image className="w-5 h-5 text-purple-600" />;
    if (mimeType?.includes('spreadsheet') || mimeType?.includes('excel')) return <FileSpreadsheet className="w-5 h-5 text-green-600" />;
    return <FileText className="w-5 h-5 text-indigo-600" />;
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Documents</h1>
      <div {...getRootProps()} className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer mb-6 transition-all ${isDragActive ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300 hover:border-gray-400'}`}>
        <input {...getInputProps()} />
        <Upload className="w-10 h-10 text-gray-400 mx-auto mb-2" />
        <p className="text-gray-600">{isDragActive ? 'Drop files here' : 'Drag & drop files or click to browse'}</p>
        <p className="text-sm text-gray-400 mt-1">PDF, Word, Excel, Images, and more</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {documents.map(doc => (
          <div key={doc.id} className="card p-4">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center">
                  {getFileIcon(doc.mime_type)}
                </div>
                <div>
                  <p className="font-medium text-gray-900 truncate max-w-[200px]">{doc.title}</p>
                  <p className="text-xs text-gray-500">{(doc.file_size / 1024).toFixed(1)} KB</p>
                </div>
              </div>
              <button onClick={() => deleteDoc(doc.id)} className="p-1.5 text-red-500 hover:bg-red-50 rounded-lg">
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
            <p className="text-xs text-gray-400 mt-2">{doc.mime_type}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

