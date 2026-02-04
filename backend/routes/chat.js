const express = require('express');
const router = express.Router();

// Get recent messages
router.get('/', async (req, res) => {
    try {
        const messages = await req.db.getMessages(50);
        res.json(messages.map(m => ({
            id: m.id,
            user: m.user_name,
            text: m.text,
            avatar: m.avatar,
            timestamp: new Date(m.timestamp).getTime()
        })));
    } catch (err) {
        console.error('Get chat error:', err);
        res.status(500).json({ error: 'Failed to fetch chat messages' });
    }
});

// Post a new message
router.post('/', async (req, res) => {
    try {
        const { user, text, avatar } = req.body;
        if (!user || !text) {
            return res.status(400).json({ error: 'User and text are required' });
        }

        const message = { user, text, avatar };
        const savedMessage = await req.db.createMessage(message);

        res.status(201).json({
            ...savedMessage,
            timestamp: new Date().getTime()
        });
    } catch (err) {
        console.error('Post chat error:', err);
        res.status(500).json({ error: 'Failed to post message' });
    }
});

module.exports = router;
