import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import logo from '../../assets/logo.png';
import './Navbar.css';

const Navbar = () => {
  const [menu, setMenu] = useState("home");

  return (
    <div className="navbar">
      <div className="nav-logo">
        <img src={logo} alt="ALERT logo" />
      </div>

      <div className="nav-right">
        <ul className="nav-menu">
          <li onClick={() => setMenu("home")}>
            <Link style={{ textDecoration: 'none', color: '#162339' }} to='/'>Home</Link>
            {menu === "home" && <hr />}
          </li>
          <li onClick={() => setMenu("about")}>
            <Link style={{ textDecoration: 'none', color: '#162339' }} to='/home'>About</Link>
            {menu === "about" && <hr />}
          </li>
          <li onClick={() => setMenu("contact")}>
            <Link style={{ textDecoration: 'none', color: '#162339' }} to='/contact'>Contact</Link>
            {menu === "contact" && <hr />}
          </li>
          <li onClick={() => setMenu("signin")}>
            <Link style={{ textDecoration: 'none', color: '#162339'}} to='/signin'>Sign In</Link>
            {menu === "signin" && <hr />}
          </li>
        </ul>
        <Link to='/login' className='nav-signup-btn'>
          <button>Sign Up</button>
        </Link>
      </div>
    </div>
  );
}

export default Navbar;
