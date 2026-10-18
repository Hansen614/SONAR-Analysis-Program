"""Explicit, traceable interpretation of the user's experimental metadata."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIRMATIONS = json.loads((ROOT / 'config/user_confirmations.json').read_text())
PROVENANCE = 'config/user_confirmations.json#USER_METADATA_20261013'

def flow_metadata(series, source_condition, replicate, acquisition_id):
    if source_condition is None:
        return {}
    common = dict(
        source_condition_label=source_condition,
        well_id=acquisition_id + '_well',
        well_identity_status='independent_transfection_well_user_confirmed',
        well_id_type='analysis_identifier_from_source_label_not_plate_coordinate',
        experimental_unit='independent_transfection_well_within_experiment',
        independent_transfection_wells_per_condition=2,
        culture_independence_verified=False,
        metadata_confirmation_source=PROVENANCE,
    )
    if series == 'S7':
        actual = CONFIRMATIONS['S7_actual_AC_mass_percent_by_source_label'][f'{source_condition:g}']
        common.update(condition_label=actual, actual_ac_mass_pct=actual,
                      ac_fraction_basis='mass', mixture_process='AC_INAC_DNA_mass_mixture_user_confirmed')
    elif series == 'S10':
        reporter = CONFIRMATIONS['S10_reporter_dna_ng_per_well']
        total = CONFIRMATIONS['S10_total_dna_ng_per_well']
        editor = reporter * source_condition
        suffixes = [k for k, v in CONFIRMATIONS['S10_molecular_suffix_to_flow_replicate'].items() if v == replicate]
        molecular_ratio = '05' if source_condition == .5 else f'{source_condition:g}'
        common.update(
            editor_construct='ORCA_P2A_BFP_user_confirmed_exact_sequence_unverified',
            editor_bfp_linked=True, reporter_dna_ng=reporter, editor_dna_ng=editor,
            total_dna_ng=total, balancing_dna_ng=total-reporter-editor,
            dose_source='reporter_total_user_confirmed_editor_derived_from_recorded_1_to_x_ratio',
            balancing_dna_source='mass_balance_derived_vector_identity_not_independently_verified',
            rna_pair_id=';'.join(f'1-{molecular_ratio}-{s}' for s in suffixes),
            RNA_origin_user_confirmed=True,
            sampling_time=CONFIRMATIONS['S10_RNA_sampling_relation'],
            flow_to_extraction_elapsed_minutes=None,
        )
    return common

def molecular_metadata(label):
    left, ratio, suffix = label.split('-')
    if left != '1':
        raise ValueError(f'Unexpected reporter ratio label: {label}')
    value = .5 if ratio == '05' else float(ratio)
    replicate = CONFIRMATIONS['S10_molecular_suffix_to_flow_replicate'][suffix]
    acquisition = f'S10_1_{value:g}_{replicate}'
    return dict(
        flow_acquisition_pair=acquisition, well_id=acquisition+'_well',
        flow_replicate=replicate, editor_ratio=value, molecular_suffix=int(suffix),
        experimental_unit='independent_transfection_well_within_experiment',
        grouped_validation_unit=acquisition+'_well',
        molecular_labels_per_well=2,
        within_well_molecular_relationship=CONFIRMATIONS['molecular_labels_within_well_subtype'],
        series_assignment='S10_pairing_confirmed_by_user_despite_s9_form_filename',
        RNA_origin_user_confirmed=True,
        RNA_origin_assay_validated=False,
        RNA_sampling_relation=CONFIRMATIONS['S10_RNA_sampling_relation'],
        flow_to_extraction_elapsed_minutes=None,
        RNA_population_selection=CONFIRMATIONS['RNA_population_selection'],
        metadata_confirmation_source=PROVENANCE,
    )
