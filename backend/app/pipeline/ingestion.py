import logging
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.pipeline.api_clients import EPAClient, DEFRAClient, IPCCClient
from app.pipeline.transformers import EmissionFactorTransformer
from app.pipeline.quality import DataQualityAssessor
from app.db.models.emissions import EmissionFactor

logger = logging.getLogger(__name__)

class DataIngestionPipeline:
    """Main data ingestion pipeline for emission factors"""
    
    def __init__(self, db: Session, epa_api_key: str = None, defra_api_key: str = None):
        self.db = db
        self.transformer = EmissionFactorTransformer()
        self.quality_assessor = DataQualityAssessor(db)
        
        # Initialize API clients
        self.epa_client = EPAClient(epa_api_key)
        self.defra_client = DEFRAClient(defra_api_key)
        self.ipcc_client = IPCCClient()
    
    def run_full_sync(self) -> Dict[str, int]:
        """Run full data synchronization from all sources"""
        logger.info("Starting full data synchronization")
        
        sync_results = {
            'total_processed': 0,
            'total_inserted': 0,
            'total_updated': 0,
            'total_errors': 0,
            'sources': {}
        }
        
        try:
            # Sync from EPA
            epa_results = self._sync_epa_data()
            sync_results['sources']['EPA'] = epa_results
            self._update_totals(sync_results, epa_results)
            
            # Sync from DEFRA
            defra_results = self._sync_defra_data()
            sync_results['sources']['DEFRA'] = defra_results
            self._update_totals(sync_results, defra_results)
            
            # Sync from IPCC
            ipcc_results = self._sync_ipcc_data()
            sync_results['sources']['IPCC'] = ipcc_results
            self._update_totals(sync_results, ipcc_results)
            
            logger.info(f"Full sync completed: {sync_results}")
            
        except Exception as e:
            logger.error(f"Full sync failed: {e}")
            sync_results['total_errors'] += 1
            raise
        
        return sync_results
    
    def _sync_epa_data(self) -> Dict[str, int]:
        """Sync data from EPA"""
        logger.info("Syncing EPA data")
        
        try:
            # Get current year data
            current_year = datetime.now().year
            raw_data = self.epa_client.get_emission_factors(current_year)
            
            return self._process_source_data(raw_data, 'EPA')
        
        except Exception as e:
            logger.error(f"Error syncing EPA data: {e}")
            return {'processed': 0, 'inserted': 0, 'updated': 0, 'errors': 1}
    
    def _sync_defra_data(self) -> Dict[str, int]:
        """Sync data from DEFRA"""
        logger.info("Syncing DEFRA data")
        
        try:
            # Get UK emission factors
            raw_data = self.defra_client.get_uk_emission_factors()
            
            return self._process_source_data(raw_data, 'DEFRA')
        
        except Exception as e:
            logger.error(f"Error syncing DEFRA data: {e}")
            return {'processed': 0, 'inserted': 0, 'updated': 0, 'errors': 1}
    
    def _sync_ipcc_data(self) -> Dict[str, int]:
        """Sync data from IPCC"""
        logger.info("Syncing IPCC data")
        
        try:
            # Get Global Warming Potentials
            raw_data = self.ipcc_client.get_global_warming_potentials('AR6')
            
            return self._process_source_data(raw_data, 'IPCC')
        
        except Exception as e:
            logger.error(f"Error syncing IPCC data: {e}")
            return {'processed': 0, 'inserted': 0, 'updated': 0, 'errors': 1}
    
    def _process_source_data(self, raw_data: List[Dict], source: str) -> Dict[str, int]:
        """Process data from a specific source"""
        results = {'processed': 0, 'inserted': 0, 'updated': 0, 'errors': 0}
        
        # Transform data
        transformed_data = self.transformer.transform(raw_data)
        results['processed'] = len(transformed_data)
        
        # Assess data quality
        quality_assessed_data = self.quality_assessor.assess_data_quality(transformed_data)
        
        # Save to database
        for factor_data in quality_assessed_data:
            try:
                is_new = self._save_emission_factor(factor_data)
                if is_new:
                    results['inserted'] += 1
                else:
                    results['updated'] += 1
            except Exception as e:
                logger.error(f"Error saving factor {factor_data.get('name')}: {e}")
                results['errors'] += 1
        
        logger.info(f"{source} sync results: {results}")
        return results
    
    def _save_emission_factor(self, factor_data: Dict) -> bool:
        """Save emission factor to database, return True if new"""
        # Check if factor already exists
        existing_factor = self.db.query(EmissionFactor).filter(
            EmissionFactor.name == factor_data['name'],
            EmissionFactor.source == factor_data['source'],
            EmissionFactor.category == factor_data['category'],
            EmissionFactor.region == factor_data['region'],
            EmissionFactor.year == factor_data['year']
        ).first()
        
        if existing_factor:
            # Update existing factor
            for key, value in factor_data.items():
                if hasattr(existing_factor, key) and key != 'metadata':
                    setattr(existing_factor, key, value)
            self.db.commit()
            return False
        else:
            # Create new factor (remove metadata for now since it might cause issues)
            factor_data_clean = {k: v for k, v in factor_data.items() if k != 'metadata'}
            new_factor = EmissionFactor(**factor_data_clean)
            self.db.add(new_factor)
            self.db.commit()
            return True
    
    def _update_totals(self, sync_results: Dict, source_results: Dict):
        """Update total counts in sync results"""
        sync_results['total_processed'] += source_results['processed']
        sync_results['total_inserted'] += source_results['inserted']
        sync_results['total_updated'] += source_results['updated']
        sync_results['total_errors'] += source_results['errors']
