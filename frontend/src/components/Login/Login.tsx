import React, { useState } from "react";
import "./Login.css";
import alertLogo from "../../assets/alert_logo.png";
import disasterBg from "../../assets/disaster-bg.png";

<div
  className="hero-container"
  style={{ backgroundImage: `url(${disasterBg})` }}
>
  {/* content */}
</div>

const Login: React.FC = () => {
  const [navActive, setNavActive] = useState(false);

  const toggleNav = () => {
    setNavActive(!navActive);
  };

  return (
    <div className="hero-container" style={{ backgroundImage: `url(${disasterBg})` }}>
      <header>
        <img src={alertLogo} alt="ALERT Logo" className="logo" />

        <nav>
          <ul className={`nav-links ${navActive ? "nav-active" : ""}`}>
            <li>
              <a href="#">Home</a>
            </li>
            <li>
              <a href="#">About</a>
            </li>
            <li>
              <a href="#">Contact</a>
            </li>
            <li>
              <a href="#" className="btn btn-signup">
                Sign Up
              </a>
            </li>
          </ul>
        </nav>

        <div
          className={`hamburger ${navActive ? "toggle" : ""}`}
          onClick={toggleNav}
        >
          <div className="line"></div>
          <div className="line"></div>
          <div className="line"></div>
        </div>
      </header>

      <main>
        <div className="hero-text">
          <h1>Stay Safe</h1>
          <h1>Stay Informed</h1>
          <h1 className="highlight-text">Stay ALERT</h1>
        </div>

        <div className="signin-form-container">
          <h2>Sign In to your Account</h2>
          <p>Enter registered email and password in the fields provided.</p>

          <form>
            <div className="input-group">
              <input
                type="email"
                id="email"
                defaultValue="your_email_@gmail.com"
                required
              />
            </div>
            <div className="input-group">
              <input
                type="password"
                id="password"
                defaultValue="------------"
                required
              />
            </div>
            <button type="submit" className="btn btn-signin">
              Sign In
            </button>
          </form>
        </div>
      </main>
    </div>
  );
};

export default Login;