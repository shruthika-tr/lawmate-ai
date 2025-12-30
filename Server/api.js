// App/project/src/api.js

// DO NOT use HuggingFace as fallback during development
const BACKEND_URL = import.meta.env.VITE_API_URL;

if (!BACKEND_URL) {
  throw new Error("VITE_API_URL is not defined. Check your .env file.");
}

console.log("BACKEND_URL =", BACKEND_URL);

export const submitForm = async (formData) => {
  const response = await fetch(`${BACKEND_URL}/submit-form`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(formData),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text);
  }

  return await response.json();
};

export const sendChatQuery = async (service, query, userId) => {
  const response = await fetch(`${BACKEND_URL}/${service}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-ID': userId,
    },
    body: JSON.stringify({ query }),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text);
  }

  return await response.json();
};

export const getChatHistory = async (service, userId) => {
  const response = await fetch(`${BACKEND_URL}/${service}/history`, {
    method: 'GET',
    headers: { 'X-User-ID': userId },
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text);
  }

  return await response.json();
};
