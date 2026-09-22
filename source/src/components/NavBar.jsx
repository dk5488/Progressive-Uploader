
import { ScrollSmoother } from "gsap/all";

const NavBar = () => {
    const handleLogoClick = () => {
        // Use ScrollSmoother if available, otherwise fallback to window.scrollTo
        if (ScrollSmoother.get()) {
            ScrollSmoother.get().scrollTo(0, false, "top top");
        } else {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    };

    return (
        <nav className="fixed top-0 left-0 z-50 md:p-9 p-3">
            <img
                src="/images/nav-logo.svg"
                alt="nav-logo"
                className="md:w-24 w-20 cursor-pointer"
                onClick={handleLogoClick}
            />
        </nav>
    );
};

export default NavBar;