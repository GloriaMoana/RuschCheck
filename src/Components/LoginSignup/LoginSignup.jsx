import React, { useState } from "react";
import './LoginSignup.css';
import { FaLock, FaEnvelope, FaUser } from "react-icons/fa";


const LoginSignup = () => {

    const [action, setAction] = useState('');



    const signupLink = (e) => {
        e.preventDefault();
        console.log("✅ signupLink clicked!");
        setAction('active');
    };

    const loginLink = (e) => {
        e.preventDefault();
        setAction('');
    };

    // const signupLink = () => {
    //     console.log("✅ signupLink clicked!");
    //     setAction('active');
    // };
    // const loginLink = () => {
    //     setAction('');
    // };


    return (
        <div>
            <h1 className="welcome-heading">Welcome to RushCheck!</h1>
            <div className={`wrapper ${action}`}>
                <div className='form-box login'>
                    <form action="">
                        <h1>Login to your account</h1>
                        <div className='input-box'>
                            <div className='text'>Email</div>
                            <input type='text' placeholder='exampe.email@gmail.com' required /><FaEnvelope className='icon' />
                        </div>
                        <div className='input-box'>
                            <div className='text'>Password</div>
                            <input type='Password' placeholder='Enter at least 8+ characters' required /><FaLock className='icon' />
                        </div>
                        <div className='remember-forgot'>
                            <label>
                                <input type='checkbox' /> Remember me
                            </label>
                            <a href='/some-valid-path'>Forgot password?</a>
                        </div>
                        <button className='submit'>Login</button>

                        <div className='Signup-link'>
                            <p> Don't have an account? <a href='/go-to-sign-up' onClick={signupLink}> Sign up</a></p>
                        </div>
                    </form>
                </div>

                <div className='form-box Signup'>
                    <form action="">
                        <h1>Sign up </h1>
                        <div className='input-box'>
                            <div className='text'>Username</div>
                            <input type='text' placeholder='Enter your username' required /><FaUser className='icon' />
                        </div>
                        <div className='input-box'>
                            <div className='text'>Email</div>
                            <input type='text' placeholder='exampe.email@gmail.com' required /><FaEnvelope className='icon' />
                        </div>
                        <div className='input-box'>
                            <div className='text'>Password</div>
                            <input type='Password' placeholder='Enter at least 8+ characters' required /><FaLock className='icon' />
                        </div>
                        <div className='input-box'>
                            <div className='text'>Confirm password</div>
                            <input type='Password' placeholder='Re-enter password' required /><FaLock className='icon' />
                        </div>
                        <div className='remember-forgot'>
                            <label>
                                <input type='checkbox' /> I argee to the term & conditions
                            </label>
                        </div>
                        <button className='submit'>Sign up</button>

                        <div className='Signup-link'>
                            <p> Alreay have an account? <a href='/go-to-login-page' onClick={loginLink}> Login</a></p>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default LoginSignup;
