import { useState } from "react";
import "./Index.css";
import alertLogo from "../../assets/alert_logo.png";
import disasterBg from "../../assets/disaster-bg.png";

const Index: React.FC = () => {
  const [navActive, setNavActive] = useState(false);

  const toggleNav = () => {
    setNavActive(!navActive);
  };

  return (
    <div className="hero-container" style={{ backgroundImage: `url(${disasterBg})` }}>
      <header>
        <div className="logo-container">
          <img src={alertLogo} alt="ALERT Logo" className="logo" />
        </div>

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
      </main>
    </div>
  );
};

export default Index;
