document.addEventListener("DOMContentLoaded", function () {
  // Check if user is logged in
  checkAuthStatus();

  // Logout functionality
  const logoutBtn = document.getElementById("logout");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", function (e) {
      e.preventDefault();
      logout();
    });
  }

  // Login form handling
  const loginForm = document.getElementById("loginForm");
  if (loginForm) {
    loginForm.addEventListener("submit", function (e) {
      e.preventDefault();
      login();
    });
  }

  // Register form handling
  const registerForm = document.getElementById("registerForm");
  if (registerForm) {
    registerForm.addEventListener("submit", function (e) {
      e.preventDefault();
      register();
    });
  }
});

async function checkAuthStatus() {
  const currentPath = window.location.pathname;
  const justLoggedIn = sessionStorage.getItem("justLoggedIn") === "true";

  // Skip auth check if we just logged in
  if (justLoggedIn) {
    sessionStorage.removeItem("justLoggedIn");
    return;
  }

  // Check if we have a valid session
  try {
    const response = await fetch("/api/check-session", {
      method: "GET",
      credentials: "include",
    });

    const data = await response.json();

    // If on auth pages and already logged in, redirect to dashboard
    if (
      (currentPath.includes("/auth/login") ||
        currentPath.includes("/auth/register")) &&
      response.ok
    ) {
      // Update local storage with user data
      if (data.user) {
        localStorage.setItem("user", JSON.stringify(data.user));
        localStorage.setItem("isAuthenticated", "true");
      }
      window.location.href = "/";
      return;
    }

    // If not on auth pages and not logged in, redirect to login
    if (!response.ok && !currentPath.includes("/auth/")) {
      localStorage.removeItem("isAuthenticated");
      window.location.href = "/auth/login";
      return;
    }

    // Update local storage with user data if we're logged in
    if (response.ok && data.user) {
      localStorage.setItem("user", JSON.stringify(data.user));
      localStorage.setItem("isAuthenticated", "true");
    }
  } catch (error) {
    console.error("Auth check error:", error);
    if (!currentPath.includes("/auth/")) {
      localStorage.removeItem("isAuthenticated");
      window.location.href = "/auth/login";
    }
  }

  // If on protected pages and not logged in, redirect to login
  const protectedPages = [
    "/",
    "/transactions",
    "/accounts",
    "/budgets",
    "/charts",
    "/game",
  ];

  // The actual authentication is handled by the try-catch block above
  // This is just an additional check for protected pages
  if (
    protectedPages.includes(currentPath) &&
    !localStorage.getItem("isAuthenticated")
  ) {
    window.location.href = "/auth/login";
  }
}

// This function is kept for backward compatibility but not used in the new flow
function verifyToken() {
  // The actual verification is now handled by the server
  // This is just a placeholder for any code that might still call this function
}

// This function is called when we need to refresh the session
async function refreshToken() {
  try {
    const response = await fetch("/auth/refresh", {
      method: "POST",
      credentials: "include",
    });

    if (!response.ok) {
      throw new Error("Session refresh failed");
    }

    // Update the last activity timestamp
    localStorage.setItem("lastActivity", Date.now().toString());
  } catch (error) {
    console.error("Session refresh error:", error);
    // If refresh fails, log the user out
    await logout();
  }
}

async function login() {
  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;

  try {
    const response = await fetch("/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password }),
      credentials: "include", // Important: This allows cookies to be sent/received
    });

    const data = await response.json();

    if (response.ok) {
      // Store user info and auth status in localStorage
      localStorage.setItem("user", JSON.stringify(data.user));
      localStorage.setItem("isAuthenticated", "true");

      // Set a flag to indicate we just logged in
      sessionStorage.setItem("justLoggedIn", "true");

      // Redirect to dashboard
      window.location.href = "/";
    } else {
      throw new Error(data.message || "Login failed");
    }
  } catch (error) {
    console.error("Login error:", error);
    alert(error.message || "Login failed. Please try again.");
  }
}

async function register() {
  const username = document.getElementById("username").value;
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;
  const confirmPassword = document.getElementById("confirmPassword").value;

  if (password !== confirmPassword) {
    alert("Passwords do not match");
    return;
  }

  try {
    const response = await fetch("/auth/register", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        username,
        email,
        password,
        confirm_password: confirmPassword,
      }),
      credentials: "include",
    });

    const data = await response.json();
    
    if (response.ok) {
      // If registration is successful, automatically log the user in
      const loginResponse = await fetch("/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
        credentials: "include",
      });

      const loginData = await loginResponse.json();
      
      if (loginResponse.ok) {
        // Store user info and auth status
        localStorage.setItem("user", JSON.stringify(loginData.user));
        localStorage.setItem("isAuthenticated", "true");
        
        // Set flag to indicate successful registration
        sessionStorage.setItem("justRegistered", "true");
        
        // Redirect to dashboard
        window.location.href = "/";
      } else {
        throw new Error(loginData.message || 'Automatic login after registration failed');
      }
    } else {
      throw new Error(data.message || 'Registration failed');
    }
  } catch (error) {
    console.error("Registration error:", error);
    alert(error.message || "Registration failed. Please try again.");
  }
}

async function logout() {
  try {
    const response = await fetch("/auth/logout", {
      method: "POST",
      credentials: "include",
    });

    // Clear all auth-related data
    localStorage.removeItem("user");
    localStorage.removeItem("isAuthenticated");
    sessionStorage.removeItem("justLoggedIn");

    // Redirect to login page
    window.location.href = "/auth/login";
  } catch (error) {
    console.error("Logout error:", error);
    // Still redirect even if there was an error
    window.location.href = "/auth/login";
  }
}
