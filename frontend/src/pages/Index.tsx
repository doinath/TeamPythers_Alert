import React from 'react';
import landingImage from '../assets/landingimage.png';

const Index = () => {
  return (
    <div
      style={{
        width: '100vw',
        height: '100vh',      
        overflow: 'hidden',     
      }}
    >
      <img
        src={landingImage}
        alt="landing"
        style={{
          width: '100vw',      
          height: '100vh',     
          objectFit: 'cover',   
          display: 'block',     
        }}
      />
    </div>
  );
};

export default Index;
