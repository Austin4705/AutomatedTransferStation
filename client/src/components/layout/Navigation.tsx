import { NavLink } from 'react-router-dom';

const Navigation = () => {
  return (
    <nav className="horizontal-navigation bg-gray-700 py-2 px-4">
      <ul className="flex space-x-6 justify-center">
        <li>
          <NavLink
            to="/dashboard"
            className={({ isActive }) =>
              isActive ? "nav-link active font-bold" : "nav-link hover:text-gray-300"
            }
          >
            Dashboard
          </NavLink>
        </li>
      </ul>
    </nav>
  );
}

export default Navigation; 