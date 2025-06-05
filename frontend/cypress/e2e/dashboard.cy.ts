describe('Dashboard E2E Tests', () => {
  beforeEach(() => {
    cy.visit('/');
    cy.viewport(1280, 720);
  });

  it('should load dashboard with charts and metrics', () => {
    cy.contains('Dashboard Overview').should('be.visible');
    cy.contains('Total Emissions').should('be.visible');
    
    // Check if charts are rendered
    cy.get('canvas').should('have.length.at.least', 2);
    
    // Check metrics cards
    cy.get('[data-testid="total-emissions"]').should('contain', 'tonnes CO2e');
  });

  it('should open form dialog when FAB is clicked', () => {
    cy.get('[aria-label="add emission record"]').click();
    cy.contains('Add Emission Record').should('be.visible');
    
    // Test form fields
    cy.get('input[name="activity_amount"]').type('100');
    cy.get('[data-testid="scope-select"]').click();
    cy.contains('Scope 1').click();
  });

  it('should export data', () => {
    cy.get('[data-testid="export-button"]').click();
    cy.contains('Export CSV').click();
    
    // Verify download (mock or check network request)
    cy.intercept('GET', '/api/export*').as('exportRequest');
    cy.wait('@exportRequest').should((interception) => {
      expect(interception.response?.statusCode).to.equal(200);
    });
  });
});
