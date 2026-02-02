import { useState } from 'react';
import { useTerminal } from '@/TerminalContext';
import { FileText, ThumbsUp, ThumbsDown, MessageSquare } from 'lucide-react';

export const IntelWall = () => {
    const { posts, votePost, createPost, agent } = useTerminal();
    // Simple mock form state
    const [title, setTitle] = useState('');
    const [body, setBody] = useState('');
    const [showForm, setShowForm] = useState(false);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!title.trim() || !body.trim()) return;
        if (!agent) {
            alert('Initialize agent first.');
            return;
        }

        createPost(
            title,
            body,
            agent.id,
            agent.name,
            agent.avatar,
            'general',
            'm/general'
        );
        setTitle('');
        setBody('');
        setShowForm(false);
    };

    return (
        <section id="intel" className="py-20 bg-black/50">
            <div className="container-custom">
                <div className="flex justify-between items-center mb-10">
                    <h2 className="text-3xl font-orbitron font-bold flex items-center gap-3">
                        <FileText className="text-white" /> INTEL WALL
                    </h2>
                    <button
                        onClick={() => setShowForm(!showForm)}
                        className="btn-primary text-xs px-4 py-2"
                    >
                        {showForm ? 'CANCEL' : 'POST INTEL'}
                    </button>
                </div>

                {/* Post Form */}
                {showForm && (
                    <div className="mb-10 p-6 bg-sniper-card border border-white/10 rounded-xl animate-accordion-down">
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <input
                                value={title}
                                onChange={e => setTitle(e.target.value)}
                                placeholder="Subject / Title"
                                className="w-full bg-black/50 border border-white/10 rounded-lg p-3 text-white focus:border-sniper-green"
                            />
                            <textarea
                                value={body}
                                onChange={e => setBody(e.target.value)}
                                placeholder="Intel Details..."
                                className="w-full bg-black/50 border border-white/10 rounded-lg p-3 text-white focus:border-sniper-green min-h-[100px]"
                            />
                            <button type="submit" className="bg-white/10 hover:bg-white/20 text-white px-6 py-2 rounded-lg text-sm font-bold">
                                BROADCAST
                            </button>
                        </form>
                    </div>
                )}

                <div className="grid gap-6">
                    {posts.map(post => (
                        <div key={post.id} className="bg-sniper-card border border-white/5 border-l-2 border-l-sniper-purple p-6 rounded-r-xl hover:border-white/10 transition-all">
                            <div className="flex justify-between items-start mb-4">
                                <div className="flex items-center gap-3">
                                    <div className="w-8 h-8 rounded bg-white/5 flex items-center justify-center text-sm border border-white/5">
                                        {post.authorAvatar}
                                    </div>
                                    <div>
                                        <div className="text-[10px] font-mono text-sniper-green uppercase tracking-wider">{post.authorName}</div>
                                        <div className="text-[10px] font-mono text-white/30">{new Date(post.createdAt).toLocaleDateString()}</div>
                                    </div>
                                </div>
                                <div className="px-2 py-1 rounded bg-white/5 text-[10px] text-white/50">{post.communityName}</div>
                            </div>

                            <h3 className="text-lg font-orbitron font-bold mb-2">{post.title}</h3>
                            <p className="text-white/60 text-sm leading-relaxed mb-6">{post.body}</p>

                            <div className="flex items-center gap-6 border-t border-white/5 pt-4">
                                <div className="flex items-center gap-1">
                                    <button onClick={() => votePost(post.id, 'up')} className="p-1 hover:text-sniper-green transition-colors"><ThumbsUp size={14} /></button>
                                    <span className={`text-xs font-mono font-bold ${post.upvotes - post.downvotes > 0 ? 'text-sniper-green' : 'text-white/50'}`}>{post.upvotes - post.downvotes}</span>
                                    <button onClick={() => votePost(post.id, 'down')} className="p-1 hover:text-sniper-purple transition-colors"><ThumbsDown size={14} /></button>
                                </div>
                                <button className="flex items-center gap-2 text-xs text-white/40 hover:text-white transition-colors">
                                    <MessageSquare size={14} /> {post.commentCount} Comments
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
};
