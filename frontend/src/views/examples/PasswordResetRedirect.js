import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

const PasswordResetRedirect = () => {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const uid = params.get('uid');
    const token = params.get('token');

    if (uid && token) {
      // Redirect to the correct frontend route that displays the form
      navigate(`/auth/reset-password/${uid}/${token}`, { replace: true });
    } else {
      // If the params are missing, just go to the login page
      navigate('/auth/reset-password/:uidb64/:token', { replace: true });
    }
  }, [navigate, location]);

  // This component renders nothing, it only handles the redirect logic.
  return null;
};

export default PasswordResetRedirect;
