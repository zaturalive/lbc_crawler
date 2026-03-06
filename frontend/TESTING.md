# Frontend Testing Guide — find_my_car

**Framework:** Jest + React Testing Library  
**Coverage:** 7 test suites, 109 tests (70% passing)

---

## 🚀 Quick Start

```bash
cd frontend

# Run all tests
npm test -- --watchAll=false

# Watch mode (recommended for development)
npm test

# Coverage report
npm test -- --coverage --watchAll=false
```

---

## 📁 Test Structure

```
frontend/src/
├── setupTests.js                    # Global test config
├── components/
│   └── __tests__/
│       ├── Header.test.jsx          ✅ 10 tests
│       ├── ListingCard.test.jsx     ✅ 19 tests
│       ├── VehicleScore.test.jsx    ✅ 21 tests
│       ├── ResultsGrid.test.jsx     ✅ 20 tests
│       ├── SearchForm.test.jsx      ⚠️  14 tests
│       └── ui.test.jsx              ⚠️  17 tests
└── api/
    └── __tests__/
        └── client.test.js           ⚠️  8 tests
```

---

## ✅ Passing Test Suites

### 1. Header.test.jsx (10 tests)
Tests pour le composant header simple.

```bash
npm test -- --testPathPattern=Header
```

**Coverage:**
- Rendering (title, subtitle, attribution)
- Styling (classes, colors, spacing)
- Layout (flexbox, max-width)

### 2. ListingCard.test.jsx (19 tests)
Tests pour l'affichage d'une annonce automobile.

```bash
npm test -- --testPathPattern=ListingCard
```

**Coverage:**
- Data rendering (title, price, year, mileage, location)
- Keywords display (badges with variants)
- VehicleScore integration
- Edge cases (missing fields, null values)
- External link behavior

### 3. VehicleScore.test.jsx (21 tests)
Tests pour le score de fiabilité avec couleurs.

```bash
npm test -- --testPathPattern=VehicleScore
```

**Coverage:**
- Score display (X.X/10 format)
- Badge variants (green ≥7, orange 4-6, red <4)
- Common issues list (limited to 3)
- Fallback states (null, undefined, no data)

### 4. ResultsGrid.test.jsx (20 tests)
Tests pour la grille de résultats.

```bash
npm test -- --testPathPattern=ResultsGrid
```

**Coverage:**
- Loading state (spinner, message)
- Empty states (null, 0 results)
- Results display (count, pluralization)
- Grid layout (responsive Tailwind)
- Large datasets (50+ results)

---

## ⚠️ In Progress Test Suites

### 5. SearchForm.test.jsx (14 tests)
Tests pour le formulaire de recherche.

**Issues:**
- Mock API complexe avec PatternSelector
- Dynamic import de `api/client` dans composant

**To Fix:**
```javascript
// Mock setupTests mieux intégré
jest.mock('./api/client', () => ({
  searchListings: jest.fn(() => Promise.resolve({})),
  getPatterns: jest.fn(() => Promise.resolve([])),
}));
```

### 6. ui.test.jsx (17 tests)
Tests pour les composants UI shadcn/ui.

**Components:**
- Button (variant, size, disabled, fullWidth)
- Input (text, number, min/max)
- Card & CardContent
- Badge (variants: success, warning, danger, blue, purple)

### 7. client.test.js (8 tests)
Tests pour l'API client.

**Coverage:**
- HTTP methods (GET, POST, DELETE)
- Request headers & body
- Response parsing
- Error handling (400, 500)
- Parameter encoding

---

## 🔧 Configuration

### setupTests.js
```javascript
import '@testing-library/jest-dom';

jest.mock('./api/client', () => ({
  searchListings: jest.fn(() => Promise.resolve({ listings: [] })),
  getPatterns: jest.fn(() => Promise.resolve([])),
  createPattern: jest.fn(() => Promise.resolve({})),
  deletePattern: jest.fn(() => Promise.resolve(null)),
  getVehicle: jest.fn(() => Promise.resolve({})),
}));
```

### package.json Scripts
```json
{
  "scripts": {
    "test": "react-scripts test",
    "test:ci": "CI=true npm test -- --watchAll=false --passWithNoTests"
  }
}
```

---

## 💡 Test Patterns Used

### 1. Rendering Tests
```javascript
it('renders component', () => {
  render(<Header />);
  expect(screen.getByText('Find My Car')).toBeInTheDocument();
});
```

### 2. User Interaction Tests
```javascript
it('submits form on button click', async () => {
  const user = userEvent.setup();
  render(<SearchForm onResults={jest.fn()} />);
  
  await user.type(screen.getByPlaceholderText('ex: Peugeot'), 'Renault');
  await user.click(screen.getByRole('button', { name: /chercher/i }));
});
```

### 3. Props & State Tests
```javascript
it('handles null vehicle gracefully', () => {
  render(<VehicleScore vehicle={null} />);
  expect(screen.queryByText(/fiabilité/i)).not.toBeInTheDocument();
});
```

### 4. API Mock Tests
```javascript
it('calls API with correct payload', async () => {
  const { searchListings } = require('../../api/client');
  searchListings.mockResolvedValueOnce({ listings: [] });
  
  await searchListings({ brand: 'Renault' });
  expect(searchListings).toHaveBeenCalledWith({ brand: 'Renault' });
});
```

---

## 📊 Test Results Summary

### Passing (70%)
- ✅ Header: 10/10
- ✅ ListingCard: 19/19
- ✅ VehicleScore: 21/21
- ✅ ResultsGrid: 20/20

### In Progress (30%)
- ⚠️ SearchForm: 6/14 passing
- ⚠️ UI Components: 10/17 passing
- ⚠️ API Client: 6/8 passing

---

## 🔍 How to Debug Tests

### Run single test file
```bash
npm test -- --testPathPattern=Header
```

### Run single test
```bash
npm test -- -t "renders brand and model inputs"
```

### Watch specific file
```bash
npm test -- --testPathPattern=ListingCard --watch
```

### See detailed errors
```bash
npm test -- --verbose
```

### Clear Jest cache
```bash
npm test -- --clearCache
```

---

## 📝 Writing New Tests

### Basic Template
```javascript
import { render, screen } from '@testing-library/react';
import MyComponent from '../MyComponent';

describe('MyComponent', () => {
  it('does something', () => {
    render(<MyComponent />);
    expect(screen.getByText('Expected Text')).toBeInTheDocument();
  });

  it('handles edge case', () => {
    render(<MyComponent prop={null} />);
    expect(screen.getByText('Fallback')).toBeInTheDocument();
  });
});
```

### Common Assertions
```javascript
// Presence
expect(element).toBeInTheDocument();
expect(screen.queryByText('text')).not.toBeInTheDocument();

// Attributes
expect(link).toHaveAttribute('href', '/path');
expect(button).toHaveClass('active');

// Values
expect(input).toHaveValue('text');
expect(screen.getByDisplayValue('initial')).toBeInTheDocument();

// State
expect(button).toBeDisabled();
expect(checkbox).toBeChecked();
```

---

## 🎯 Next Steps

### To Improve Coverage
1. Fix SearchForm + PatternSelector mock
2. Stabilize UI Components with class selectors
3. Refactor API client mock with MSW (Mock Service Worker)
4. Add integration tests for App.jsx
5. Add E2E tests with Cypress/Playwright

### To Run Coverage Report
```bash
npm test -- --coverage --watchAll=false
```

---

## 📚 Resources

- [React Testing Library Docs](https://testing-library.com/react)
- [Jest API Reference](https://jestjs.io/docs/api)
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)

---

**Last Updated:** 2024  
**Framework Version:** Jest + React Testing Library (via create-react-app)
