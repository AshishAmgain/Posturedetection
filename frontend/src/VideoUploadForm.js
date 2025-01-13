const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setFeedback(null);

    try {
        const formData = new FormData();
        formData.append('video', videoFile);
        formData.append('username', username);

        const response = await fetch('http://localhost:5000/upload', {
            method: 'POST',
            body: formData,
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || `Upload failed with status: ${response.status}`);
        }

        setFeedback(data.feedback);
        fetchLeaderboard();  // Refresh leaderboard after successful upload
    } catch (err) {
        console.error('Upload error:', err);
        setError(err.message || 'Failed to upload video');
    } finally {
        setLoading(false);
    }
}; 