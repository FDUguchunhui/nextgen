# UniProt Human Protein JSON Downloader

This script downloads all human proteins from the UniProt REST API and saves them as a comprehensive JSON file. Each protein record contains all available information from UniProt.

## Features

- Downloads all reviewed human proteins (Swiss-Prot entries) 
- Uses the official UniProt REST API
- Handles pagination automatically with cursor-based navigation
- Saves complete protein information including:
  - Basic identifiers (accession, name, ID)
  - Protein descriptions and names
  - Gene information
  - Functional annotations (comments)
  - Sequence data
  - Cross-references to other databases
  - Keywords and GO terms
  - References and citations
  - Feature annotations
  - And much more...

## Query Used

The script uses the query: `(reviewed:true) AND (organism_id:9606)`

This retrieves:
- **reviewed:true**: Only manually curated Swiss-Prot entries (high quality)
- **organism_id:9606**: Human proteins only (Homo sapiens)

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the script:
```bash
python uniprot_json_downloader.py
```

The script will:
1. Connect to the UniProt REST API
2. Download all human protein data in batches
3. Save the complete dataset to `human_proteins_uniprot.json`
4. Display download statistics

## Output Format

The output JSON file has the following structure:

```json
{
  "metadata": {
    "query": "(reviewed:true) AND (organism_id:9606)",
    "total_proteins": 20394,
    "download_timestamp": "2024-01-15 10:30:45 UTC",
    "description": "Human proteins from UniProt (reviewed Swiss-Prot entries)",
    "source": "UniProt REST API",
    "base_url": "https://rest.uniprot.org"
  },
  "proteins": [
    {
      "primaryAccession": "P04217",
      "uniProtkbId": "A2GL_HUMAN",
      "entryType": "UniProtKB reviewed (Swiss-Prot)",
      "proteinDescription": {
        "recommendedName": {
          "fullName": {
            "value": "Alpha-2-HS-glycoprotein"
          }
        }
      },
      "organism": {
        "scientificName": "Homo sapiens",
        "commonName": "Human",
        "taxonId": 9606
      },
      "sequence": {
        "value": "MKSLVLLLLLLLLLPLLGKVQGKLCP...",
        "length": 367,
        "molWeight": 39324
      },
      "comments": [
        {
          "commentType": "FUNCTION",
          "texts": [
            {
              "value": "Promotes endocytosis..."
            }
          ]
        }
      ],
      "keywords": [...],
      "uniProtKBCrossReferences": [...],
      "references": [...],
      "features": [...]
    }
  ]
}
```

## Data Fields Available

Each protein record contains comprehensive information:

### Basic Information
- `primaryAccession`: UniProt accession number
- `uniProtkbId`: UniProt entry name
- `entryType`: Type of entry (Swiss-Prot/TrEMBL)
- `proteinExistence`: Evidence level for protein existence

### Protein Description
- `proteinDescription`: Recommended and alternative names
- `organism`: Organism information (name, taxonomy)
- `genes`: Gene names and synonyms

### Functional Information
- `comments`: Functional annotations (function, subcellular location, etc.)
- `keywords`: Controlled vocabulary keywords
- `features`: Sequence features and domains

### Sequence Data
- `sequence`: Amino acid sequence and properties
  - `value`: The actual sequence
  - `length`: Sequence length
  - `molWeight`: Molecular weight

### External Links
- `uniProtKBCrossReferences`: Links to other databases (GO, PDB, etc.)
- `references`: Literature citations

## Example Usage

```python
import json

# Load the downloaded data
with open('human_proteins_uniprot.json', 'r') as f:
    data = json.load(f)

proteins = data['proteins']

# Find proteins by name
insulin_proteins = [
    p for p in proteins 
    if 'insulin' in p.get('proteinDescription', {})
        .get('recommendedName', {})
        .get('fullName', {})
        .get('value', '').lower()
]

# Get protein by accession
def get_protein_by_accession(accession):
    for protein in proteins:
        if protein.get('primaryAccession') == accession:
            return protein
    return None

# Extract sequences
sequences = {}
for protein in proteins:
    acc = protein.get('primaryAccession')
    seq = protein.get('sequence', {}).get('value')
    if acc and seq:
        sequences[acc] = seq
```

## Statistics

The script typically downloads:
- ~20,000+ reviewed human proteins
- Complete functional annotations
- Sequence information for all proteins
- Cross-references to 100+ databases
- Literature citations and evidence

## Notes

- The download may take several minutes depending on network speed
- The resulting JSON file is typically 200-500 MB
- Rate limiting is implemented to be respectful to the UniProt servers
- Only reviewed (Swiss-Prot) entries are downloaded for highest quality

## Error Handling

The script includes:
- Automatic retry on network errors
- Rate limiting to avoid overwhelming the server
- Comprehensive logging
- Graceful handling of incomplete data

## License

This script is for educational and research purposes. The UniProt data is distributed under the Creative Commons Attribution (CC BY 4.0) License.

## Citation

If you use UniProt data in your research, please cite:
- UniProt Consortium. UniProt: the universal protein knowledgebase in 2023. Nucleic Acids Res. 51:D523-D531 (2023)
