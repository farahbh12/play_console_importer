import React, { useState, useEffect } from 'react';
import teamService from '../../services/teamService';

const TeamManagement = () => {
    const [members, setMembers] = useState([]);
    const [email, setEmail] = useState('');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    useEffect(() => {
        fetchMembers();
    }, []);

    const fetchMembers = async () => {
        try {
            const response = await teamService.getMembers();
            setMembers(response.data);
        } catch (error) {
            setError('Failed to fetch team members.');
        }
    };

    const handleInvite = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');
        try {
            const response = await teamService.inviteMember(email);
            setSuccess(response.data.message);
            setEmail('');
            fetchMembers(); // Refresh the list
        } catch (error) {
            setError(error.response?.data?.error || 'Failed to send invitation.');
        }
    };

    return (
        <div>
            <h2>Team Management</h2>
            
            <form onSubmit={handleInvite}>
                <h3>Invite New Member</h3>
                <input 
                    type="email" 
                    value={email} 
                    onChange={(e) => setEmail(e.target.value)} 
                    placeholder="Enter email address" 
                    required 
                />
                <button type="submit">Send Invitation</button>
                {error && <p style={{color: 'red'}}>{error}</p>}
                {success && <p style={{color: 'green'}}>{success}</p>}
            </form>

            <hr />

            <h3>Team Members</h3>
            <ul>
                {members.map(member => (
                    <li key={member.id}>
                        {member.first_name} {member.last_name} ({member.email}) - {member.role_client}
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default TeamManagement;
