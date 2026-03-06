import { render, screen } from '@testing-library/react';
import Header from '../Header';

describe('Header Component', () => {
  it('renders main title', () => {
    render(<Header />);
    expect(screen.getByText('Find My Car')).toBeInTheDocument();
  });

  it('renders subtitle in French', () => {
    render(<Header />);
    expect(screen.getByText(/trouvez la voiture/i)).toBeInTheDocument();
  });

  it('renders "Powered by LBC" attribution', () => {
    render(<Header />);
    expect(screen.getByText(/powered by lbc/i)).toBeInTheDocument();
  });

  it('renders as header element', () => {
    const { container } = render(<Header />);
    expect(container.querySelector('header')).toBeInTheDocument();
  });

  it('applies header styling classes', () => {
    const { container } = render(<Header />);
    const header = container.querySelector('header');
    expect(header).toHaveClass('border-b');
    expect(header).toHaveClass('bg-white');
    expect(header).toHaveClass('shadow-sm');
  });

  it('applies responsive padding classes', () => {
    const { container } = render(<Header />);
    const headerContent = container.querySelector('header > div');
    expect(headerContent).toHaveClass('px-4');
    expect(headerContent).toHaveClass('sm:px-6');
    expect(headerContent).toHaveClass('lg:px-8');
  });

  it('applies max-width constraint', () => {
    const { container } = render(<Header />);
    const headerContent = container.querySelector('header > div');
    expect(headerContent).toHaveClass('max-w-7xl');
  });

  it('renders title with bold font weight', () => {
    const { container } = render(<Header />);
    const title = container.querySelector('h1');
    expect(title).toHaveClass('font-bold');
  });

  it('renders subtitle with smaller text size', () => {
    const { container } = render(<Header />);
    const subtitle = container.querySelector('p');
    expect(subtitle).toHaveClass('text-sm');
  });

  it('displays title and subtitle side by side with attribution', () => {
    const { container } = render(<Header />);
    const flexContainer = container.querySelector('header > div');
    expect(flexContainer).toHaveClass('flex');
    expect(flexContainer).toHaveClass('justify-between');
  });

  it('applies neutral color styling', () => {
    const { container } = render(<Header />);
    const title = container.querySelector('h1');
    expect(title).toHaveClass('text-neutral-900');
  });
});
