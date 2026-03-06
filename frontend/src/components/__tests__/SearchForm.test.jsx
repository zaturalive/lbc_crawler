import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SearchForm from '../SearchForm';
import * as apiClient from '../../api/client';

jest.mock('../../api/client', () => ({
  searchListings: jest.fn(),
  getPatterns: jest.fn(),
  createPattern: jest.fn(),
  deletePattern: jest.fn(),
}));

describe('SearchForm Component', () => {
  const mockOnResults = jest.fn();
  const mockOnLoading = jest.fn();

  beforeEach(() => {
    mockOnResults.mockClear();
    mockOnLoading.mockClear();
    // Reset API mock implementations (not clearAllMocks which can clear implementations)
    apiClient.searchListings.mockResolvedValue({ listings: [] });
    apiClient.getPatterns.mockResolvedValue([]);
    if (apiClient.createPattern) apiClient.createPattern.mockResolvedValue({});
    if (apiClient.deletePattern) apiClient.deletePattern.mockResolvedValue(null);
  });

  describe('Rendering', () => {
    it('renders all input fields', () => {
      render(<SearchForm onResults={mockOnResults} onLoading={mockOnLoading} />);

      // Multiple empty inputs exist — check at least one
      expect(screen.getAllByDisplayValue('').length).toBeGreaterThan(0);
      expect(screen.getByText('Marque')).toBeInTheDocument();
      expect(screen.getByText('Modèle')).toBeInTheDocument();
      expect(screen.getByText('Boîte de vitesses')).toBeInTheDocument();
      expect(screen.getByText(/Prix min/i)).toBeInTheDocument();
      expect(screen.getByText(/Prix max/i)).toBeInTheDocument();
      expect(screen.getByText(/Kilométrage max/i)).toBeInTheDocument();
      expect(screen.getByText(/Année min/i)).toBeInTheDocument();
      expect(screen.getByText(/Chevaux min/i)).toBeInTheDocument();
      expect(screen.getByText(/Chevaux max/i)).toBeInTheDocument();
    });

    it('renders submit button with text "Chercher"', () => {
      render(<SearchForm onResults={mockOnResults} onLoading={mockOnLoading} />);
      const button = screen.getByRole('button', { name: /chercher/i });
      expect(button).toBeInTheDocument();
    });

    it('renders PatternSelector component', () => {
      render(<SearchForm onResults={mockOnResults} onLoading={mockOnLoading} />);
      // PatternSelector renders "Filtrer par mots-clés" or the advanced mode button
      expect(screen.getByText(/mots-clés/i) || screen.getByText(/mode avancé/i)).toBeInTheDocument();
    });
  });

  describe('Form Input Handling', () => {
    it('updates form state when typing in brand input', async () => {
      const user = userEvent.setup();
      render(<SearchForm onResults={mockOnResults} onLoading={mockOnLoading} />);

      const brandInput = screen.getByPlaceholderText('ex: Peugeot');
      await user.type(brandInput, 'Renault');
      expect(brandInput).toHaveValue('Renault');
    });

    it('updates form state when typing in model input', async () => {
      const user = userEvent.setup();
      render(<SearchForm onResults={mockOnResults} onLoading={mockOnLoading} />);

      const modelInput = screen.getByPlaceholderText('ex: 308');
      await user.type(modelInput, 'Clio');
      expect(modelInput).toHaveValue('Clio');
    });

    it('updates numeric fields correctly', async () => {
      const user = userEvent.setup();
      render(<SearchForm onResults={mockOnResults} onLoading={mockOnLoading} />);

      const priceMinInput = screen.getByPlaceholderText('0');
      await user.type(priceMinInput, '5000');
      expect(priceMinInput).toHaveValue(5000);
    });
  });

  describe('Submit Behavior', () => {
    it('shows loading state while searching', async () => {
      const user = userEvent.setup();
      render(<SearchForm onResults={mockOnResults} onLoading={mockOnLoading} />);

      const submitButton = screen.getByRole('button', { name: /chercher/i });
      const brandInput = screen.getByPlaceholderText('ex: Peugeot');

      await user.type(brandInput, 'Peugeot');
      await user.click(submitButton);

      expect(mockOnLoading).toHaveBeenCalledWith(true);
    });

    it('calls onLoading(false) after search completes', async () => {
      const user = userEvent.setup();
      
      apiClient.searchListings.mockResolvedValueOnce({ listings: [] });

      render(<SearchForm onResults={mockOnResults} onLoading={mockOnLoading} />);

      const submitButton = screen.getByRole('button', { name: /chercher/i });
      const brandInput = screen.getByPlaceholderText('ex: Peugeot');

      await user.type(brandInput, 'Peugeot');
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnLoading).toHaveBeenCalledWith(false);
      });
    });

    it('calls searchListings with correct payload', async () => {
      const user = userEvent.setup();
      
      apiClient.searchListings.mockResolvedValueOnce({ listings: [] });

      render(<SearchForm onResults={mockOnResults} onLoading={mockOnLoading} />);

      const brandInput = screen.getByPlaceholderText('ex: Peugeot');
      const modelInput = screen.getByPlaceholderText('ex: 308');
      const submitButton = screen.getByRole('button', { name: /chercher/i });

      await user.type(brandInput, 'Renault');
      await user.type(modelInput, 'Clio');
      await user.click(submitButton);

      await waitFor(() => {
        expect(apiClient.searchListings).toHaveBeenCalledWith(
          expect.objectContaining({
            brand: 'Renault',
            model: 'Clio',
          })
        );
      });
    });
  });

  describe('Error Handling', () => {
    it('displays error message when API call fails', async () => {
      const user = userEvent.setup();
      
      const errorMessage = 'API Error: Server not available';
      apiClient.searchListings.mockRejectedValueOnce(new Error(errorMessage));

      render(<SearchForm onResults={mockOnResults} onLoading={mockOnLoading} />);

      const brandInput = screen.getByPlaceholderText('ex: Peugeot');
      const submitButton = screen.getByRole('button', { name: /chercher/i });

      await user.type(brandInput, 'Renault');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
      });
    });

    it('calls onResults(null) when search fails', async () => {
      const user = userEvent.setup();
      
      apiClient.searchListings.mockRejectedValueOnce(new Error('Network error'));

      render(<SearchForm onResults={mockOnResults} onLoading={mockOnLoading} />);

      const brandInput = screen.getByPlaceholderText('ex: Peugeot');
      const submitButton = screen.getByRole('button', { name: /chercher/i });

      await user.type(brandInput, 'Renault');
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnResults).toHaveBeenCalledWith(null);
      });
    });
  });
});
