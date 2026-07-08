export const API_CONFIG = {
  gateway: process.env.NEXT_PUBLIC_API_GATEWAY || 'http://localhost:8080',
  useMock: process.env.NEXT_PUBLIC_USE_MOCK === 'true',

  services: {
    security: '/security',
    admin: '/administracion',
    tutorias: '/tutorias',
    chatbot: '/chatbot',
  },
};