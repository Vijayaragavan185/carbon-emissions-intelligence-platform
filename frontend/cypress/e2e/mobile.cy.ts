describe('Mobile Dashboard Tests', () => {
  beforeEach(() => {
    cy.viewport(375, 667); // Mobile viewport
    cy.visit('/');
  });

  it('should display mobile-optimized dashboard', () => {
    // Check mobile navigation
    cy.get('[aria-label="open drawer"]').should('be.visible');
    
    // Charts should adapt to mobile
    cy.get('canvas').should('be.visible');
    
    // FAB should be positioned for mobile
    cy.get('[aria-label="add emission record"]')
      .should('be.visible')
      .should('have.css', 'position', 'fixed');
  });

  it('should open sidebar on mobile', () => {
    cy.get('[aria-label="open drawer"]').click();
    cy.contains('Dashboard').should('be.visible');
    cy.contains('Reports').should('be.visible');
  });
});
