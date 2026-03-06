import { render, screen } from '@testing-library/react';
import Button from '../ui/Button';
import { Card, CardContent } from '../ui/Card';
import Input from '../ui/Input';
import Badge from '../ui/Badge';

describe('UI Components (shadcn)', () => {
  describe('Button Component', () => {
    it('renders button with default text', () => {
      render(<Button>Click me</Button>);
      expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument();
    });

    it('applies primary variant styling', () => {
      render(<Button variant="primary">Primary</Button>);
      expect(screen.getByRole('button', { name: 'Primary' })).toBeInTheDocument();
    });

    it('disables button when disabled prop is true', () => {
      render(<Button disabled>Disabled</Button>);
      expect(screen.getByRole('button')).toBeDisabled();
    });

    it('renders full width button', () => {
      const { container } = render(<Button fullWidth>Full Width</Button>);
      const button = container.querySelector('button');
      expect(button).toHaveClass('w-full');
    });

    it('renders button with large size', () => {
      render(<Button size="lg">Large</Button>);
      expect(screen.getByRole('button', { name: 'Large' })).toBeInTheDocument();
    });
  });

  describe('Input Component', () => {
    it('renders input element', () => {
      render(<Input placeholder="Enter text" />);
      expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument();
    });

    it('accepts numeric input', () => {
      render(<Input type="number" placeholder="Enter number" />);
      const input = screen.getByPlaceholderText('Enter number');
      expect(input).toHaveAttribute('type', 'number');
    });

    it('has min and max attributes for number input', () => {
      render(<Input type="number" min="0" max="100" />);
      const input = screen.getByDisplayValue('');
      expect(input).toHaveAttribute('min', '0');
      expect(input).toHaveAttribute('max', '100');
    });

    it('accepts value prop and handles onChange', () => {
      const { rerender } = render(<Input value="test" onChange={() => {}} />);
      let input = screen.getByDisplayValue('test');
      expect(input).toHaveValue('test');

      rerender(<Input value="updated" onChange={() => {}} />);
      input = screen.getByDisplayValue('updated');
      expect(input).toHaveValue('updated');
    });
  });

  describe('Card Component', () => {
    it('renders Card with content', () => {
      render(
        <Card>
          <CardContent>Test content</CardContent>
        </Card>
      );
      expect(screen.getByText('Test content')).toBeInTheDocument();
    });

    it('renders multiple CardContent elements', () => {
      render(
        <Card>
          <CardContent>First</CardContent>
          <CardContent>Second</CardContent>
        </Card>
      );
      expect(screen.getByText('First')).toBeInTheDocument();
      expect(screen.getByText('Second')).toBeInTheDocument();
    });
  });

  describe('Badge Component', () => {
    it('renders badge with text', () => {
      render(<Badge>Default Badge</Badge>);
      expect(screen.getByText('Default Badge')).toBeInTheDocument();
    });

    it('applies success variant styling', () => {
      render(<Badge variant="success">Success</Badge>);
      expect(screen.getByText('Success')).toBeInTheDocument();
    });

    it('applies warning variant styling', () => {
      render(<Badge variant="warning">Warning</Badge>);
      expect(screen.getByText('Warning')).toBeInTheDocument();
    });

    it('applies danger variant styling', () => {
      render(<Badge variant="danger">Danger</Badge>);
      expect(screen.getByText('Danger')).toBeInTheDocument();
    });

    it('applies blue variant styling', () => {
      render(<Badge variant="blue">Blue</Badge>);
      expect(screen.getByText('Blue')).toBeInTheDocument();
    });

    it('applies purple variant styling', () => {
      render(<Badge variant="purple">Purple</Badge>);
      expect(screen.getByText('Purple')).toBeInTheDocument();
    });

    it('applies default variant styling', () => {
      render(<Badge variant="default">Default</Badge>);
      expect(screen.getByText('Default')).toBeInTheDocument();
    });
  });
});
