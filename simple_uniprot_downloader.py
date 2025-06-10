#!/usr/bin/env python3
"""
Simple UniProt TSV Downloader with Pagination

A UniProt downloader that uses direct REST API calls to retrieve protein data
in TSV format with comprehensive field coverage and proper pagination.
"""

import requests
import csv
import io
import time
import logging
from typing import Dict, List, Any, Optional
from urllib.parse import urlencode
from tqdm import tqdm


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleUniProtTSVDownloader:
    """
    Simple UniProt downloader using direct REST API calls with TSV format and pagination
    """
    
    BASE_URL = "https://rest.uniprot.org"
    
    # Comprehensive list of UniProt return fields
    ALL_FIELDS = [
        # Core identifiers
        'accession', 'id', 'gene_names', 'gene_primary', 'gene_synonym', 
        'gene_oln', 'gene_orf', 'organism_name', 'organism_id', 'protein_name',
        'xref_proteomes', 'lineage', 'lineage_ids', 'virus_hosts',
        
        # Sequence information
        'cc_alternative_products', 'ft_var_seq', 'error_gmodel_pred', 'fragment', 
        'organelle', 'length', 'mass', 'cc_mass_spectrometry', 'ft_variant', 
        'ft_non_cons', 'ft_non_std', 'ft_non_ter', 'cc_polymorphism', 
        'cc_rna_editing', 'sequence', 'cc_sequence_caution', 'ft_conflict', 
        'ft_unsure', 'sequence_version',
        
        # Function
        'absorption', 'ft_act_site', 'cc_activity_regulation', 'ft_binding', 
        'cc_catalytic_activity', 'cc_cofactor', 'ft_dna_bind', 'ec', 'cc_function', 
        'kinetics', 'cc_pathway', 'ph_dependence', 'redox_potential', 'rhea', 
        'ft_site', 'temp_dependence',
        
        # Miscellaneous
        'annotation_score', 'cc_caution', 'comment_count', 'feature_count', 
        'keywordid', 'keyword', 'cc_miscellaneous', 'protein_existence', 
        'reviewed', 'tools', 'uniparc_id',
        
        # Interaction
        'cc_interaction', 'cc_subunit',
        
        # Expression
        'cc_developmental_stage', 'cc_induction', 'cc_tissue_specificity',
        
        # Gene Ontology
        'go_p', 'go_c', 'go', 'go_f', 'go_id',
        
        # Pathology & Biotech
        'cc_allergen', 'cc_biotechnology', 'cc_disruption_phenotype', 'cc_disease', 
        'ft_mutagen', 'cc_pharmaceutical', 'cc_toxic_dose',
        
        # Subcellular location
        'ft_intramem', 'cc_subcellular_location', 'ft_topo_dom', 'ft_transmem',
        
        # PTM / Processing
        'ft_chain', 'ft_crosslnk', 'ft_disulfid', 'ft_carbohyd', 'ft_init_met', 
        'ft_lipid', 'ft_mod_res', 'ft_peptide', 'cc_ptm', 'ft_propep', 
        'ft_signal', 'ft_transit',
        
        # Structure
        'structure_3d', 'ft_strand', 'ft_helix', 'ft_turn',
        
        # Publications
        'lit_pubmed_id',
        
        # Date information
        'date_created', 'date_modified', 'date_sequence_modified', 'version',
        
        # Family & Domains
        'ft_coiled', 'ft_compbias', 'cc_domain', 'ft_domain', 'ft_motif', 
        'protein_families', 'ft_region', 'ft_repeat', 'ft_zn_fing'
    ]
    
    def __init__(self, output_file: str = "uniprot_proteins.tsv"):
        self.output_file = output_file
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SimpleUniProtTSVDownloader/2.0 (TSV Format)'
        })
        
    def download_proteins_tsv_paginated(self, query: str, batch_size: int = 500) -> int:
        """Download proteins using UniProt search API with pagination and save to TSV file"""
        
        search_url = f"{self.BASE_URL}/uniprotkb/search"
        
        # Create fields string from available fields
        fields = ','.join(self.ALL_FIELDS)
        
        params = {
            'query': query,
            'format': 'tsv',
            'fields': fields,
            'size': batch_size
        }
        
        total_proteins = 0
        first_batch = True
        cursor = None
        
        # Open output file for writing
        with open(self.output_file, 'w', newline='', encoding='utf-8') as outfile:
            writer = None
            
            while True:
                # Add cursor for pagination (except first request)
                if cursor:
                    params['cursor'] = cursor
                elif 'cursor' in params:
                    del params['cursor']
                    
                logger.info(f"Downloading batch with cursor: {cursor if cursor else 'None'}")
                
                try:
                    response = self.session.get(search_url, params=params)
                    response.raise_for_status()
                    
                    # Parse TSV data
                    tsv_data = response.text.strip()
                    if not tsv_data:
                        logger.info("No more data available")
                        break
                    
                    # Parse the TSV data
                    csv_reader = csv.reader(io.StringIO(tsv_data), delimiter='\t')
                    rows = list(csv_reader)
                    
                    if not rows:
                        logger.info("No rows in response")
                        break
                    
                    # Write header only for the first batch
                    if first_batch:
                        header = rows[0]
                        writer = csv.writer(outfile, delimiter='\t')
                        writer.writerow(header)
                        first_batch = False
                        data_rows = rows[1:]  # Skip header
                    else:
                        data_rows = rows[1:] if len(rows) > 1 and rows[0] == header else rows
                    
                    # Write data rows
                    for row in data_rows:
                        writer.writerow(row)
                    
                    batch_count = len(data_rows)
                    total_proteins += batch_count
                    logger.info(f"Downloaded {batch_count} proteins in this batch (total: {total_proteins})")
                    
                    # Check for next page cursor in response headers
                    link_header = response.headers.get('Link', '')
                    cursor = None
                    
                    if link_header:
                        # Parse Link header to find next cursor
                        for link in link_header.split(','):
                            if 'rel="next"' in link:
                                # Extract cursor from the URL
                                link_part = link.split(';')[0].strip('<> ')
                                if 'cursor=' in link_part:
                                    cursor = link_part.split('cursor=')[1].split('&')[0]
                                break
                    
                    # If no cursor found or we got less than requested size, we're done
                    if not cursor or batch_count < batch_size:
                        logger.info("Reached end of results")
                        break
                        
                except requests.exceptions.RequestException as e:
                    logger.error(f"Request error: {e}")
                    break
                except Exception as e:
                    logger.error(f"Error in download: {e}")
                    break
                    
                # Rate limiting
                time.sleep(0.1)
                
        logger.info(f"Downloaded {total_proteins} total proteins to {self.output_file}")
        return total_proteins

    def download_human_canonical_proteins(self):
        """Download human canonical proteins using TSV format with pagination"""
        
        logger.info("Starting download of human canonical proteins using TSV format")
        
        # Search for human reviewed proteins
        query = "reviewed:true AND organism_id:9606"
        
        try:
            # Download protein data in TSV format with pagination
            total_count = self.download_proteins_tsv_paginated(query, batch_size=500)
            
            if total_count == 0:
                logger.error("No proteins found with the specified query")
                return
            
            logger.info(f"Successfully downloaded {total_count} human canonical proteins")
            logger.info(f"TSV file saved to: {self.output_file}")
            
        except Exception as e:
            logger.error(f"Error during download: {e}")
            raise

    def get_file_stats(self) -> Dict[str, Any]:
        """Get basic statistics about the downloaded TSV file"""
        try:
            with open(self.output_file, 'r', encoding='utf-8') as file:
                reader = csv.reader(file, delimiter='\t')
                header = next(reader)
                row_count = sum(1 for _ in reader)
                
            return {
                'total_proteins': row_count,
                'columns': len(header),
                'file_size_mb': round(
                    __import__('os').path.getsize(self.output_file) / (1024 * 1024), 2
                )
            }
        except FileNotFoundError:
            return {'error': f'File {self.output_file} not found'}
        except Exception as e:
            return {'error': f'Error reading file: {e}'}


def main():
    """Main function"""
    
    output_file = "human_canonical_proteins.tsv"
    downloader = SimpleUniProtTSVDownloader(output_file)
    
    print("UniProt TSV Downloader with Pagination")
    print("=====================================")
    print("Downloads UniProt data in TSV format using batch size 500")
    print()
    
    try:
        # Download proteins
        downloader.download_human_canonical_proteins()
        
        # Show statistics
        print("\nDownload Statistics:")
        print("===================")
        stats = downloader.get_file_stats()
        
        if 'error' in stats:
            print(f"Error: {stats['error']}")
        else:
            print(f"Total proteins: {stats['total_proteins']}")
            print(f"Number of columns: {stats['columns']}")
            print(f"File size: {stats['file_size_mb']} MB")
            print(f"TSV file saved to: {output_file}")
        
        # Show sample of the data
        print(f"\nSample data from {output_file}:")
        print("=" * 50)
        try:
            with open(output_file, 'r', encoding='utf-8') as file:
                reader = csv.reader(file, delimiter='\t')
                header = next(reader)
                
                # Show first few columns of header
                print("Columns (first 10):", header[:10])
                print()
                
                # Show first few rows
                for i, row in enumerate(reader):
                    if i >= 3:  # Show only first 3 data rows
                        break
                    print(f"Row {i+1} (first 3 fields): {row[:3]}")
        except Exception as e:
            print(f"Error reading sample data: {e}")
        
    except KeyboardInterrupt:
        print("\nDownload interrupted by user.")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main() 