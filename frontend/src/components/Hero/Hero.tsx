import React from 'react'
import rescuer from '../../assets/rescuer.png'

const Hero = () => {
  return (
    <div>
        <div className="hero">
            <div className="hero-left">
                <img src={rescuer} alt="Rescuer" />
            </div>
            <div className="hero-right">
                <h1>Stay Safe</h1>
                <h1>Stay Informed</h1>
                <div className="hero-msg">
                   <div className="stay">
                    <h1>Stay</h1>
                   </div>
                   <div className="alert">
                    <h1>ALERT</h1>
                   </div>
                </div>
            </div>
        </div>
    </div>
  )
}

export default Hero