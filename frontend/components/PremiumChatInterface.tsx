'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { 
  sendChatMessage, 
  uploadPDFs, 
  checkHealth, 
  getDocuments, 
  type ChatMessage, 
  type HealthResponse, 
  type DocumentInfo 
} from '../app/api';

// ============================================
// CUSTOM STYLES & ANIMATIONS
// ============================================

const customStyles = `
  @keyframes fadeInUp {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
  }
  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }
  @keyframes slideInLeft {
    from { opacity: 0; transform: translateX(-16px); }
    to { opacity: 1; transform: translateX(0); }
  }
  @keyframes slideInRight {
    from { opacity: 0; transform: translateX(16px); }
    to { opacity: 1; transform: translateX(0); }
  }
  @keyframes pulse-soft {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
  }
  @keyframes gradient-shift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
  }
  @keyframes bounce-gentle {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-4px); }
  }
  .animate-fade-in-up { animation: fadeInUp 0.4s ease-out forwards; }
  .animate-fade-in { animation: fadeIn 0.3s ease-out forwards; }
  .animate-slide-in-left { animation: slideInLeft 0.35s ease-out forwards; }
  .animate-slide-in-right { animation: slideInRight 0.35s ease-out forwards; }
  .animate-pulse-soft { animation: pulse-soft 2s ease-in-out infinite; }
  .animate-gradient { 
    background-size: 200% 200%;
    animation: gradient-shift 3s ease infinite;
  }
  .animate-bounce-gentle { animation: bounce-gentle 2s ease-in-out infinite; }
  
  .glass-effect {
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
  }
  
  .hover-lift {
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  }
  .hover-lift:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px -5px rgba(99, 102, 241, 0.25);
  }
  
  .input-glow:focus-within {
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15), 0 4px 20px -2px rgba(99, 102, 241, 0.2);
  }
`;

// ============================================
// TYPES & INTERFACES
// ============================================

interface PremiumChatInterfaceProps {
  health: HealthResponse | null;
  onHealthUpdate: (health: HealthResponse) => void;
  onRequestHealthCheck?: () => void;
}

interface Session {
  id: string;
  name: string;
  messages: ChatMessage[];
  timestamp: number;
  documentsUploaded: boolean;
  sessionDocuments: string[];
  activeDocument: string | null;
  isNamed: boolean;
}

const DOCUMENT_SPECIFIC_KEYWORDS = [
  'summarize', 'summary', 'summarise', 'explain', 'analyze', 'analyse',
  'what does', 'tell me about', 'describe', 'overview',
  'this document', 'the document', 'this file', 'the file', 'this pdf', 'the pdf'
];

// ============================================
// PREMIUM ICON COMPONENTS
// ============================================

const Icons = {
  Plus: () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
    </svg>
  ),
  Menu: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
    </svg>
  ),
  Send: () => (
    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
      <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
    </svg>
  ),
  Paperclip: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M18.375 12.739l-7.693 7.693a4.5 4.5 0 01-6.364-6.364l10.94-10.94A3 3 0 1119.5 7.372L8.552 18.32m.009-.01l-.01.01m5.699-9.941l-7.81 7.81a1.5 1.5 0 002.112 2.13" />
    </svg>
  ),
  Document: () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
    </svg>
  ),
  Upload: () => (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
    </svg>
  ),
  Close: () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
    </svg>
  ),
  Trash: () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
    </svg>
  ),
  Chat: () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 8.511c.884.284 1.5 1.128 1.5 2.097v4.286c0 1.136-.847 2.1-1.98 2.193-.34.027-.68.052-1.02.072v3.091l-3-3c-1.354 0-2.694-.055-4.02-.163a2.115 2.115 0 01-.825-.242m9.345-8.334a2.126 2.126 0 00-.476-.095 48.64 48.64 0 00-8.048 0c-1.131.094-1.976 1.057-1.976 2.192v4.286c0 .837.46 1.58 1.155 1.951m9.345-8.334V6.637c0-1.621-1.152-3.026-2.76-3.235A48.455 48.455 0 0011.25 3c-2.115 0-4.198.137-6.24.402-1.608.209-2.76 1.614-2.76 3.235v6.226c0 1.621 1.152 3.026 2.76 3.235.577.075 1.157.14 1.74.194V21l4.155-4.155" />
    </svg>
  ),
  Sparkles: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
    </svg>
  ),
  Scale: () => (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v17.25m0 0c-1.472 0-2.882.265-4.185.75M12 20.25c1.472 0 2.882.265 4.185.75M18.75 4.97A48.416 48.416 0 0012 4.5c-2.291 0-4.545.16-6.75.47m13.5 0c1.01.143 2.01.317 3 .52m-3-.52l2.62 10.726c.122.499-.106 1.028-.589 1.202a5.988 5.988 0 01-2.031.352 5.988 5.988 0 01-2.031-.352c-.483-.174-.711-.703-.59-1.202L18.75 4.971zm-16.5.52c.99-.203 1.99-.377 3-.52m0 0l2.62 10.726c.122.499-.106 1.028-.589 1.202a5.989 5.989 0 01-2.031.352 5.989 5.989 0 01-2.031-.352c-.483-.174-.711-.703-.59-1.202L5.25 4.971z" />
    </svg>
  ),
  PDF: () => (
    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zm-1 2l5 5h-5V4zM8.5 13H10v4.5H8.5V13zm3 0h1.5l1.5 2.25V13h1.5v4.5h-1.5l-1.5-2.25v2.25H11.5V13zm5 0H18a1.5 1.5 0 011.5 1.5v1.5A1.5 1.5 0 0118 17.5h-1.5v-4.5zm1.5 1.5v1.5h.5v-1.5h-.5z"/>
    </svg>
  ),
  User: () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
    </svg>
  ),
  Bot: () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
    </svg>
  ),
  Check: () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
    </svg>
  ),
  Quote: () => (
    <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
      <path d="M14.017 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10h-9.983zm-14.017 0v-7.391c0-5.704 3.748-9.57 9-10.609l.996 2.151c-2.433.917-3.996 3.638-3.996 5.849h3.983v10h-9.983z" />
    </svg>
  ),
  ChevronRight: () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
    </svg>
  ),
  Sidebar: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25H12" />
    </svg>
  ),
};

// ============================================
// MAIN COMPONENT
// ============================================

export default function PremiumChatInterface({ 
  health, 
  onHealthUpdate, 
  onRequestHealthCheck 
}: PremiumChatInterfaceProps) {
  // State
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string | null>(null);
  const [availableDocuments, setAvailableDocuments] = useState<DocumentInfo[]>([]);
  const [selectedDocumentFilter, setSelectedDocumentFilter] = useState<string | null>(null);
  const [showSidebar, setShowSidebar] = useState(true);
  const [showDocumentPicker, setShowDocumentPicker] = useState(false);
  const [pendingQuery, setPendingQuery] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Suppress unused variable warnings
  void health;
  void onRequestHealthCheck;

  // ============================================
  // INITIALIZATION & EFFECTS
  // ============================================

  // Inject custom styles
  useEffect(() => {
    const styleId = 'premium-chat-styles';
    if (!document.getElementById(styleId)) {
      const styleEl = document.createElement('style');
      styleEl.id = styleId;
      styleEl.textContent = customStyles;
      document.head.appendChild(styleEl);
    }
  }, []);

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  useEffect(() => {
    if (isMobile) setShowSidebar(false);
  }, [isMobile]);

  useEffect(() => {
    if (sessions.length === 0) {
      createNewSession();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 150) + 'px';
    }
  }, [input]);

  // ============================================
  // SESSION MANAGEMENT
  // ============================================

  const generateSessionName = (documentName?: string): string => {
    if (documentName) {
      const name = documentName.replace(/\.pdf$/i, '').substring(0, 30);
      return name.length < documentName.replace(/\.pdf$/i, '').length ? name + '...' : name;
    }
    return 'New conversation';
  };

  const saveCurrentSession = useCallback(() => {
    if (activeSessionId && messages.length > 0) {
      setSessions(prev => prev.map(session => 
        session.id === activeSessionId 
          ? { 
              ...session, 
              messages, 
              documentsUploaded: availableDocuments.length > 0,
              sessionDocuments: availableDocuments.map(d => d.filename),
              activeDocument: selectedDocumentFilter
            } 
          : session
      ));
    }
  }, [activeSessionId, messages, availableDocuments, selectedDocumentFilter]);

  const createNewSession = () => {
    saveCurrentSession();
    const newSession: Session = {
      id: `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      name: 'New conversation',
      messages: [],
      timestamp: Date.now(),
      documentsUploaded: false,
      sessionDocuments: [],
      activeDocument: null,
      isNamed: false
    };
    setSessions(prev => [newSession, ...prev]);
    setActiveSessionId(newSession.id);
    setMessages([]);
    setAvailableDocuments([]);
    setSelectedDocumentFilter(null);
    setShowDocumentPicker(false);
    setPendingQuery(null);
    if (isMobile) setShowSidebar(false);
  };

  const switchSession = async (sessionId: string) => {
    if (sessionId === activeSessionId) return;
    saveCurrentSession();
    const session = sessions.find(s => s.id === sessionId);
    if (session) {
      setActiveSessionId(sessionId);
      setMessages(session.messages);
      setSelectedDocumentFilter(session.activeDocument);
      setShowDocumentPicker(false);
      setPendingQuery(null);
      
      if (session.documentsUploaded && session.sessionDocuments.length > 0) {
        try {
          const status = await checkHealth(sessionId);
          onHealthUpdate(status);
          const docsResponse = await getDocuments(sessionId);
          setAvailableDocuments(docsResponse.documents);
        } catch {
          setAvailableDocuments([]);
        }
      } else {
        setAvailableDocuments([]);
      }
    }
    if (isMobile) setShowSidebar(false);
  };

  const deleteSession = (sessionId: string) => {
    setSessions(prev => {
      const updated = prev.filter(s => s.id !== sessionId);
      if (sessionId === activeSessionId) {
        if (updated.length > 0) {
          switchSession(updated[0].id);
        } else {
          createNewSession();
        }
      }
      return updated;
    });
  };

  // ============================================
  // DOCUMENT HANDLING
  // ============================================

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    const files = Array.from(e.dataTransfer.files).filter(f => f.type === 'application/pdf');
    if (files.length > 0) await handleUpload(files);
  };

  const handleFileInput = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) await handleUpload(files);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleUpload = async (files: File[]) => {
    if (!activeSessionId) return;
    
    setUploading(true);
    setUploadProgress(`Uploading ${files.length} file${files.length > 1 ? 's' : ''}...`);
    
    try {
      const result = await uploadPDFs(files, activeSessionId);
      
      const currentSession = sessions.find(s => s.id === activeSessionId);
      if (currentSession && !currentSession.isNamed && files.length > 0) {
        const docName = generateSessionName(files[0].name);
        setSessions(prev => prev.map(session =>
          session.id === activeSessionId 
            ? { ...session, name: docName, isNamed: true }
            : session
        ));
      }
      
      setUploadProgress('Processing documents...');
      const status = await checkHealth(activeSessionId);
      onHealthUpdate(status);
      
      const docsResponse = await getDocuments(activeSessionId);
      setAvailableDocuments(docsResponse.documents);
      
      setSessions(prev => prev.map(session =>
        session.id === activeSessionId 
          ? { ...session, documentsUploaded: true, sessionDocuments: docsResponse.documents.map(d => d.filename) }
          : session
      ));
      
      addSystemMessage(`✓ ${result.files_processed} document${result.files_processed > 1 ? 's' : ''} uploaded successfully`);
    } catch (error) {
      addSystemMessage(`Upload failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setUploading(false);
      setUploadProgress(null);
    }
  };

  const handleDocumentSelect = (filename: string) => {
    setSelectedDocumentFilter(filename);
    setShowDocumentPicker(false);
    setSessions(prev => prev.map(session =>
      session.id === activeSessionId ? { ...session, activeDocument: filename } : session
    ));
    
    if (pendingQuery) {
      executeQuery(pendingQuery, [filename]);
      setPendingQuery(null);
    }
  };

  // ============================================
  // CHAT FUNCTIONALITY
  // ============================================

  const addSystemMessage = (content: string) => {
    const systemMessage: ChatMessage = { role: 'assistant', content };
    setMessages(prev => [...prev, systemMessage]);
  };

  const isDocumentSpecificQuery = (query: string): boolean => {
    const lowerQuery = query.toLowerCase();
    return DOCUMENT_SPECIFIC_KEYWORDS.some(keyword => lowerQuery.includes(keyword));
  };

  const executeQuery = async (query: string, documentFilter?: string[]) => {
    if (!activeSessionId) return;
    
    const userMessage: ChatMessage = { role: 'user', content: query };
    setMessages(prev => [...prev, userMessage]);
    setLoading(true);

    try {
      const response = await sendChatMessage(query, 4, documentFilter, activeSessionId);
      
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        citations: response.citations,
        risk_level: response.risk_level,
        risk_reason: response.risk_reason,
        documents_used: response.documents_used
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      addSystemMessage(`Error: ${error instanceof Error ? error.message : 'Something went wrong'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || loading || uploading) return;
    
    const currentInput = input.trim();
    setInput('');
    
    const currentSession = sessions.find(s => s.id === activeSessionId);
    if (currentSession && !currentSession.isNamed) {
      const docName = availableDocuments.length > 0 ? availableDocuments[0].filename : undefined;
      const sessionName = generateSessionName(docName) || currentInput.substring(0, 30);
      setSessions(prev => prev.map(session =>
        session.id === activeSessionId 
          ? { ...session, name: sessionName, isNamed: true }
          : session
      ));
    }
    
    if (availableDocuments.length > 1 && isDocumentSpecificQuery(currentInput) && !selectedDocumentFilter) {
      setPendingQuery(currentInput);
      setShowDocumentPicker(true);
      const pickerMessage: ChatMessage = {
        role: 'assistant',
        content: 'Which document would you like me to analyze?',
        isDocumentPicker: true
      };
      setMessages(prev => [...prev, { role: 'user', content: currentInput }, pickerMessage]);
      return;
    }
    
    const filter = selectedDocumentFilter ? [selectedDocumentFilter] : undefined;
    await executeQuery(currentInput, filter);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearDocumentFilter = () => {
    setSelectedDocumentFilter(null);
    setSessions(prev => prev.map(session =>
      session.id === activeSessionId ? { ...session, activeDocument: null } : session
    ));
  };

  // ============================================
  // COMPUTED VALUES
  // ============================================

  const hasDocuments = availableDocuments.length > 0;

  // ============================================
  // SUB-COMPONENTS
  // ============================================

  const DocumentPicker = () => (
    <div className="mt-4 space-y-2">
      {availableDocuments.map((doc, idx) => (
        <button
          key={idx}
          onClick={() => handleDocumentSelect(doc.filename)}
          className="w-full flex items-center gap-3 p-4 bg-gradient-to-r from-white to-slate-50 hover:from-purple-50 hover:to-indigo-50 rounded-xl border border-slate-200/60 hover:border-purple-300 transition-all duration-300 group hover:shadow-lg hover:-translate-y-0.5"
        >
          <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-rose-500 to-pink-600 flex items-center justify-center shadow-lg shadow-rose-200/50 group-hover:scale-110 transition-transform duration-300">
            <span className="text-white"><Icons.PDF /></span>
          </div>
          <div className="flex-1 text-left min-w-0">
            <p className="font-semibold text-slate-800 truncate text-sm group-hover:text-purple-700 transition-colors">{doc.filename}</p>
            <p className="text-xs text-slate-500">{doc.page_count} pages</p>
          </div>
          <span className="text-slate-300 group-hover:text-purple-500 group-hover:translate-x-1 transition-all duration-300">
            <Icons.ChevronRight />
          </span>
        </button>
      ))}
      <button
        onClick={() => { setShowDocumentPicker(false); setPendingQuery(null); if (pendingQuery) executeQuery(pendingQuery); }}
        className="w-full p-3 text-sm text-purple-600 hover:text-purple-700 hover:bg-purple-50 rounded-xl transition-all duration-200 font-semibold"
      >
        Search all documents instead
      </button>
    </div>
  );

  const getRiskConfig = (riskLevel?: string) => {
    if (!riskLevel) return null;
    if (riskLevel.toLowerCase().includes('high')) {
      return { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700', icon: '🔴' };
    }
    if (riskLevel.toLowerCase().includes('medium')) {
      return { bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-700', icon: '🟡' };
    }
    return null;
  };

  const MessageBubble = ({ message }: { message: ChatMessage }) => {
    const isUser = message.role === 'user';
    const riskConfig = getRiskConfig(message.risk_level);
    
    return (
      <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 shadow-lg transition-transform duration-300 hover:scale-110 ${
          isUser 
            ? 'bg-gradient-to-br from-violet-500 via-purple-500 to-fuchsia-500' 
            : 'bg-gradient-to-br from-cyan-500 via-blue-500 to-indigo-600'
        }`}>
          <span className="text-white drop-shadow-sm">
            {isUser ? <Icons.User /> : <Icons.Sparkles />}
          </span>
        </div>

        <div className={`flex-1 max-w-[80%] ${isUser ? 'flex flex-col items-end' : ''}`}>
          <div className={`rounded-2xl px-4 py-3 transition-all duration-300 hover:shadow-lg ${
            isUser 
              ? 'bg-gradient-to-br from-violet-500 via-purple-500 to-fuchsia-500 text-white shadow-lg shadow-purple-200/50' 
              : 'bg-white/90 glass-effect border border-slate-200/60 text-slate-700 shadow-md hover:border-blue-200'
          }`}>
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
          </div>

          {!isUser && message.isDocumentPicker && showDocumentPicker && <DocumentPicker />}

          {!isUser && message.documents_used && message.documents_used.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {message.documents_used.map((doc, idx) => (
                <span 
                  key={idx} 
                  className="inline-flex items-center gap-1 px-2.5 py-1 bg-gradient-to-r from-blue-50 to-indigo-50 text-blue-600 rounded-full text-xs border border-blue-200/50 hover:border-blue-300 transition-colors"
                >
                  <Icons.Document />
                  <span className="truncate max-w-[120px]">{doc}</span>
                </span>
              ))}
            </div>
          )}

          {!isUser && riskConfig && (
            <div className={`mt-3 p-3 rounded-xl ${riskConfig.bg} ${riskConfig.border} border backdrop-blur-sm`}>
              <div className="flex items-center gap-2">
                <span className="text-lg">{riskConfig.icon}</span>
                <span className={`text-sm font-semibold ${riskConfig.text}`}>{message.risk_level}</span>
              </div>
              {message.risk_reason && (
                <p className={`text-xs mt-1.5 ${riskConfig.text} opacity-80 leading-relaxed`}>{message.risk_reason}</p>
              )}
            </div>
          )}
        </div>
      </div>
    );
  };

  const TypingIndicator = () => (
    <div className="flex gap-3">
      <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500 via-blue-500 to-indigo-600 flex items-center justify-center shadow-lg">
        <span className="text-white"><Icons.Sparkles /></span>
      </div>
      <div className="bg-white/90 glass-effect border border-slate-200/60 rounded-2xl px-5 py-3 shadow-md">
        <div className="flex gap-1.5">
          <span className="w-2 h-2 bg-gradient-to-r from-blue-400 to-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
          <span className="w-2 h-2 bg-gradient-to-r from-indigo-400 to-purple-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
          <span className="w-2 h-2 bg-gradient-to-r from-purple-400 to-fuchsia-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
        </div>
      </div>
    </div>
  );

  const EmptyState = () => (
    <div className="flex flex-col items-center justify-center h-full py-12">
      {!hasDocuments ? (
        <div className="w-full max-w-sm mx-auto text-center">
          <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-violet-500 via-purple-500 to-fuchsia-500 flex items-center justify-center mx-auto mb-6 shadow-2xl shadow-purple-300/50">
            <span className="text-white text-2xl"><Icons.Scale /></span>
          </div>
          <h2 className="text-2xl font-bold bg-gradient-to-r from-slate-800 via-purple-700 to-indigo-700 bg-clip-text text-transparent mb-3">Legal AI Assistant</h2>
          <p className="text-slate-500 text-sm mb-8 leading-relaxed">Upload legal documents to get AI-powered analysis with intelligent insights</p>
          
          <div 
            className={`border-2 border-dashed rounded-2xl p-10 cursor-pointer transition-all duration-300 hover-lift ${
              dragActive 
                ? 'border-purple-500 bg-purple-50/80 scale-[1.02]' 
                : 'border-slate-300 hover:border-purple-400 hover:bg-gradient-to-br hover:from-purple-50/50 hover:to-indigo-50/50'
            }`}
            onClick={() => fileInputRef.current?.click()}
          >
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-100 to-indigo-100 flex items-center justify-center mx-auto mb-4 transition-transform duration-300 group-hover:scale-110">
              <span className="text-purple-500"><Icons.Upload /></span>
            </div>
            <p className="font-semibold text-slate-700 mb-1">Drop PDFs here</p>
            <p className="text-sm text-slate-400">or click to browse</p>
          </div>
        </div>
      ) : (
        <div className="w-full max-w-md mx-auto">
          <div className="bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50 rounded-2xl p-6 border border-emerald-200/60 mb-6 shadow-lg shadow-emerald-100/50">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 via-teal-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-emerald-200/50">
                <span className="text-white"><Icons.Check /></span>
              </div>
              <div>
                <p className="font-bold text-emerald-800">{availableDocuments.length} document{availableDocuments.length > 1 ? 's' : ''} ready</p>
                <p className="text-sm text-emerald-600/80">Ask anything about your documents</p>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              {availableDocuments.map((doc, idx) => (
                <button
                  key={idx}
                  onClick={() => handleDocumentSelect(doc.filename)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white/80 hover:bg-white border border-emerald-300/60 hover:border-emerald-400 rounded-xl text-sm text-emerald-700 transition-all duration-200 hover:shadow-md hover:-translate-y-0.5"
                >
                  <span className="text-rose-500"><Icons.PDF /></span>
                  <span className="truncate max-w-[140px]">{doc.filename}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            {[
              { icon: '📋', text: 'Summarize', full: 'Summarize this document', color: 'from-blue-50 to-indigo-50 hover:from-blue-100 hover:to-indigo-100 border-blue-200/50 hover:border-blue-300' },
              { icon: '⚖️', text: 'Key clauses', full: 'What are the key clauses?', color: 'from-purple-50 to-violet-50 hover:from-purple-100 hover:to-violet-100 border-purple-200/50 hover:border-purple-300' },
              { icon: '⚠️', text: 'Risks', full: 'Identify potential risks', color: 'from-amber-50 to-orange-50 hover:from-amber-100 hover:to-orange-100 border-amber-200/50 hover:border-amber-300' },
              { icon: '💰', text: 'Obligations', full: 'List all obligations', color: 'from-emerald-50 to-teal-50 hover:from-emerald-100 hover:to-teal-100 border-emerald-200/50 hover:border-emerald-300' },
            ].map((q, idx) => (
              <button
                key={idx}
                onClick={() => setInput(q.full)}
                className={`flex items-center gap-3 p-4 bg-gradient-to-br ${q.color} rounded-xl border text-left transition-all duration-300 hover:shadow-lg hover:-translate-y-1 group`}
              >
                <span className="text-xl transition-transform duration-300 group-hover:scale-125">{q.icon}</span>
                <span className="text-sm text-slate-700 font-medium">{q.text}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  // ============================================
  // MAIN RENDER
  // ============================================

  return (
    <div 
      className="flex h-full bg-gradient-to-br from-slate-50 via-white to-purple-50/30"
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
    >
      {/* Drag Overlay */}
      {dragActive && (
        <div className="fixed inset-0 bg-purple-500/10 backdrop-blur-md z-50 flex items-center justify-center">
          <div className="bg-white/95 glass-effect rounded-3xl p-12 shadow-2xl shadow-purple-300/30 text-center border border-purple-200/50">
            <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-violet-500 via-purple-500 to-fuchsia-500 flex items-center justify-center mx-auto mb-5 shadow-2xl shadow-purple-300/50">
              <span className="text-white text-2xl"><Icons.Upload /></span>
            </div>
            <h3 className="text-xl font-bold text-slate-800 mb-2">Drop to upload</h3>
            <p className="text-sm text-slate-500">Release to analyze your documents</p>
          </div>
        </div>
      )}

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".pdf"
        onChange={handleFileInput}
        className="hidden"
      />

      {/* Sidebar */}
      <aside className={`
        ${showSidebar ? 'w-72' : 'w-0'} 
        transition-all duration-300 ease-out overflow-hidden
        bg-gradient-to-b from-slate-900 via-slate-900 to-indigo-950
        ${isMobile ? 'fixed inset-y-0 left-0 z-40' : 'relative'}
      `}>
        <div className="flex flex-col h-full w-72">
          {/* Sidebar Header */}
          <div className="p-4 border-b border-white/10">
            <button
              onClick={createNewSession}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 text-white rounded-xl text-sm font-semibold transition-all duration-300 shadow-lg shadow-purple-900/30 hover:shadow-purple-500/40 hover:-translate-y-0.5"
            >
              <Icons.Plus />
              <span>New chat</span>
            </button>
          </div>

          {/* Sessions */}
          <div className="flex-1 overflow-y-auto p-3 space-y-1">
            {sessions.map((session) => (
              <div
                key={session.id}
                onClick={() => switchSession(session.id)}
                className={`group flex items-center gap-3 px-3 py-3 rounded-xl cursor-pointer transition-all duration-200 ${
                  session.id === activeSessionId 
                    ? 'bg-gradient-to-r from-violet-600/20 to-purple-600/20 text-white border border-purple-500/30' 
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <span className={`transition-colors ${session.id === activeSessionId ? 'text-purple-400' : 'opacity-60'}`}>
                  <Icons.Chat />
                </span>
                <span className="flex-1 text-sm truncate font-medium">{session.name}</span>
                <button
                  onClick={(e) => { e.stopPropagation(); deleteSession(session.id); }}
                  className="opacity-0 group-hover:opacity-100 p-1.5 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-all duration-200"
                >
                  <Icons.Trash />
                </button>
              </div>
            ))}
          </div>

          {/* Sidebar Footer - Documents */}
          {availableDocuments.length > 0 && (
            <div className="p-4 border-t border-white/10 bg-black/20">
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-3 px-1 font-semibold">Documents</p>
              <div className="space-y-1 max-h-32 overflow-y-auto">
                {availableDocuments.map((doc, idx) => (
                  <div
                    key={idx}
                    onClick={() => handleDocumentSelect(doc.filename)}
                    className="flex items-center gap-2 px-3 py-2 text-xs text-slate-400 hover:text-white hover:bg-white/5 rounded-xl cursor-pointer transition-all duration-200 group"
                  >
                    <span className="text-rose-400 group-hover:text-rose-300"><Icons.PDF /></span>
                    <span className="truncate">{doc.filename}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </aside>

      {/* Mobile Overlay */}
      {isMobile && showSidebar && (
        <div 
          className="fixed inset-0 bg-black/50 z-30"
          onClick={() => setShowSidebar(false)}
        />
      )}

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Top Bar */}
        <header className="flex items-center justify-between px-4 py-3 bg-white/70 glass-effect border-b border-slate-200/50 sticky top-0 z-10">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowSidebar(!showSidebar)}
              className="p-2.5 text-slate-500 hover:text-purple-600 hover:bg-purple-50 rounded-xl transition-all duration-200"
            >
              <Icons.Sidebar />
            </button>
            
            {/* App Name */}
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-md">
                <Icons.Scale />
              </div>
              <div className="hidden sm:block">
                <h1 className="text-sm font-bold text-slate-800">Legal AI</h1>
                <p className="text-[10px] text-slate-500 -mt-0.5">Document Analysis</p>
              </div>
            </div>

            {selectedDocumentFilter && (
              <div className="flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-purple-50 to-indigo-50 text-purple-700 rounded-full text-xs font-semibold border border-purple-200/60 shadow-sm">
                <Icons.Document />
                <span className="truncate max-w-[150px]">{selectedDocumentFilter}</span>
                <button onClick={clearDocumentFilter} className="hover:text-purple-900 ml-1 hover:bg-purple-100 rounded-full p-0.5 transition-colors">
                  <Icons.Close />
                </button>
              </div>
            )}
          </div>
          <div className="flex items-center gap-2 text-xs">
            {hasDocuments ? (
              <span className="flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-emerald-50 to-teal-50 text-emerald-700 rounded-full border border-emerald-200/60 font-semibold shadow-sm">
                <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
                {availableDocuments.length} doc{availableDocuments.length > 1 ? 's' : ''}
              </span>
            ) : (
              <span className="flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-amber-50 to-orange-50 text-amber-700 rounded-full border border-amber-200/60 font-semibold">
                <span className="w-2 h-2 bg-amber-500 rounded-full"></span>
                No docs
              </span>
            )}
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
            {messages.length === 0 ? (
              <EmptyState />
            ) : (
              <>
                {messages.map((message, index) => (
                  <MessageBubble key={index} message={message} />
                ))}
                {loading && <TypingIndicator />}
              </>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="p-5 bg-gradient-to-t from-white via-white to-transparent">
          <div className="max-w-3xl mx-auto">
            {uploadProgress && (
              <div className="mb-4 flex items-center gap-3 text-sm text-purple-600 bg-purple-50 px-4 py-2.5 rounded-xl border border-purple-200/50 animate-fade-in">
                <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                <span className="font-semibold">{uploadProgress}</span>
              </div>
            )}
            
            <div className="flex items-end gap-3 bg-white rounded-2xl shadow-xl shadow-slate-200/50 border border-slate-200/60 p-2.5 input-glow transition-all duration-300">
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                className="p-3 text-slate-400 hover:text-purple-600 hover:bg-purple-50 rounded-xl transition-all duration-200 disabled:opacity-50"
                title="Upload PDF"
              >
                <Icons.Paperclip />
              </button>
              
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder={hasDocuments ? "Ask about your documents..." : "Upload a document to get started..."}
                disabled={loading || uploading}
                rows={1}
                className="flex-1 px-2 py-3 bg-transparent text-slate-800 placeholder-slate-400 resize-none focus:outline-none text-sm leading-relaxed"
                style={{ maxHeight: '150px' }}
              />
              
              <button
                onClick={handleSend}
                disabled={!input.trim() || loading || uploading || !hasDocuments}
                className="p-3 bg-gradient-to-r from-violet-600 to-purple-600 text-white rounded-xl hover:from-violet-500 hover:to-purple-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-300 shadow-lg shadow-purple-200/50 disabled:shadow-none hover:shadow-purple-300/60 hover:-translate-y-0.5 disabled:hover:translate-y-0"
              >
                <Icons.Send />
              </button>
            </div>
            
            <p className="text-xs text-slate-400 text-center mt-4 font-medium">
              {hasDocuments 
                ? '⌨️ Press Enter to send • Shift+Enter for new line' 
                : '📄 Upload PDF documents to start analysis'
              }
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
