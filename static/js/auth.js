/* ===============================================================
   Serene Minds - Student Wellness System
   Authentication Scripts (Student & Counselor Portals)
   Strict Authentication: No mock/demo bypass buttons allowed.
   =============================================================== */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Student Login Form
  const studentLoginForm = document.getElementById('student-login-form');
  if (studentLoginForm) {
    studentLoginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const errorBox = document.getElementById('login-error-alert');
      const submitBtn = studentLoginForm.querySelector('button[type="submit"]');
      
      const email = document.getElementById('login-email').value.trim();
      const password = document.getElementById('login-password').value;

      if (!email || !password) {
        showError(errorBox, 'Please enter both your email address and password.');
        return;
      }

      submitBtn.disabled = true;
      submitBtn.textContent = 'Authenticating...';
      if (errorBox) errorBox.style.display = 'none';

      try {
        const res = await API.post('/api/auth/login', { email, password });
        showToast(res.message || 'Login successful! Redirecting...', 'success');
        setTimeout(() => {
          window.location.href = res.redirect || '/student/dashboard';
        }, 600);
      } catch (err) {
        showError(errorBox, err.message || 'Invalid email or password.');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Sign In';
      }
    });
  }

  // 2. Student Registration Form
  const registerForm = document.getElementById('student-register-form');
  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const errorBox = document.getElementById('register-error-alert');
      const submitBtn = registerForm.querySelector('button[type="submit"]');

      const full_name = document.getElementById('reg-name').value.trim();
      const student_id = document.getElementById('reg-studentid').value.trim();
      const email = document.getElementById('reg-email').value.trim();
      const department = document.getElementById('reg-department').value;
      const academic_year = document.getElementById('reg-year').value;
      const password = document.getElementById('reg-password').value;
      const confirm_password = document.getElementById('reg-confirm-password').value;
      const phone = document.getElementById('reg-phone') ? document.getElementById('reg-phone').value.trim() : '';
      const emergency_contact = document.getElementById('reg-emergency') ? document.getElementById('reg-emergency').value.trim() : '';

      if (!full_name || !student_id || !email || !department || !password) {
        showError(errorBox, 'Please fill in all required fields.');
        return;
      }

      if (password !== confirm_password) {
        showError(errorBox, 'Passwords do not match.');
        return;
      }

      if (password.length < 6) {
        showError(errorBox, 'Password must be at least 6 characters long.');
        return;
      }

      submitBtn.disabled = true;
      submitBtn.textContent = 'Creating Account...';
      if (errorBox) errorBox.style.display = 'none';

      try {
        const payload = {
          full_name,
          student_id,
          email,
          department,
          academic_year,
          password,
          phone,
          emergency_contact
        };
        const res = await API.post('/api/auth/register', payload);
        showToast('Registration complete! Welcome to Serene Minds.', 'success');
        setTimeout(() => {
          window.location.href = res.redirect || '/student/dashboard';
        }, 700);
      } catch (err) {
        showError(errorBox, err.message || 'Registration failed. Please check your information.');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Register Student Account';
      }
    });
  }

  // 3. Counselor Strict Login Form
  const counselorLoginForm = document.getElementById('counselor-login-form');
  if (counselorLoginForm) {
    counselorLoginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const errorBox = document.getElementById('counselor-error-alert');
      const submitBtn = counselorLoginForm.querySelector('button[type="submit"]');

      const email = document.getElementById('counselor-email').value.trim();
      const password = document.getElementById('counselor-password').value;

      if (!email || !password) {
        showError(errorBox, 'Counselor email and password are required.');
        return;
      }

      submitBtn.disabled = true;
      submitBtn.textContent = 'Verifying Counselor Credentials...';
      if (errorBox) errorBox.style.display = 'none';

      try {
        const res = await API.post('/api/auth/counselor-login', { email, password });
        showToast('Counselor authorization confirmed.', 'success');
        setTimeout(() => {
          window.location.href = res.redirect || '/counselor/dashboard';
        }, 600);
      } catch (err) {
        showError(errorBox, err.message || 'Access denied. Invalid counselor credentials.');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Authorize & Enter Counselor Portal';
      }
    });
  }

  // Form toggles (Login <-> Register on student auth page)
  const toggleToRegister = document.getElementById('toggle-to-register');
  const toggleToLogin = document.getElementById('toggle-to-login');
  const loginSection = document.getElementById('login-panel');
  const registerSection = document.getElementById('register-panel');

  if (toggleToRegister && toggleToLogin && loginSection && registerSection) {
    toggleToRegister.addEventListener('click', (e) => {
      e.preventDefault();
      loginSection.style.display = 'none';
      registerSection.style.display = 'block';
    });
    toggleToLogin.addEventListener('click', (e) => {
      e.preventDefault();
      registerSection.style.display = 'none';
      loginSection.style.display = 'block';
    });
  }
});

function showError(box, message) {
  if (!box) {
    showToast(message, 'error');
    return;
  }
  box.textContent = message;
  box.style.display = 'block';
}

async function logoutUser() {
  try {
    const res = await API.post('/api/auth/logout', {});
    window.location.href = res.redirect || '/';
  } catch (e) {
    window.location.href = '/';
  }
}
