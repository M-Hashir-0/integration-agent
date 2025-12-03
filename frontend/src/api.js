import axios from 'axios';

// Connect to the FastAPI backend
const api = axios.create({
    baseURL: 'http://127.0.0.1:8000/api',
    headers: {
        'Content-Type': 'application/json',
    },
});

export const addIntegration = async (name, specUrl, apiKey) =>
{
    const response = await api.post('/integrations', {
        name,
        spec_url: specUrl,
        api_key: apiKey || null,
    });
    return response.data;
};

export const sendMessage = async (message, threadId = "default") =>
{
    const response = await api.post('/chat', {
        message,
        thread_id: threadId,
    });
    return response.data;
};