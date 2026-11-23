"""Plain-language water-law notes per state (general information, not legal advice)."""
APPROP = ("Prior appropriation: spring water belongs to whoever holds a recorded water right, and that right can be owned "
          "separately from the land. A springhead without a right attached may come with little more than household use, "
          "so check the state's water-rights records for the spring before buying.")
RIPARIAN = ("Riparian state: the owner of the land may make reasonable use of water that rises on it, shared with "
            "neighbors downstream. Ordinary household and farm use needs no permit.")
LAW = {
    "FL": ["Water belongs to the state. Household use is exempt, but pumping more, including bottling, needs a consumptive-use "
           "permit from the regional water management district, and owning the spring doesn't guarantee one. Florida also sets "
           "minimum flows for major springs.", "https://floridadep.gov/owper/water-policy"],
    "TX": ["Groundwater belongs to the landowner under the rule of capture, limited by the local groundwater conservation district. "
           "Once spring water flows into a creek it becomes state surface water, and diverting it beyond household and livestock "
           "use needs a water right from TCEQ.", "https://www.tceq.texas.gov/gis/water-rights-viewer"],
    "MO": [RIPARIAN + " Users of 100,000 gallons a day or more must register with the Missouri DNR.", "https://dnr.mo.gov/"],
    "AR": [RIPARIAN + " Diversions from streams must be registered each year with the state's Natural Resources Division.",
           "https://www.agriculture.arkansas.gov/natural-resources/divisions/water-management/groundwater-protection-and-management-program/water-use-registration/"],
    "KY": [RIPARIAN + " Withdrawals over 10,000 gallons a day need a permit from the Kentucky Division of Water.", "https://eec.ky.gov/Environmental-Protection/Water/Protection/Pages/WaterWithdrawal.aspx"],
    "TN": [RIPARIAN + " Withdrawals of 10,000 gallons a day or more must be registered with TDEC.", "https://www.tn.gov/environment/program-areas/wr-water-resources/water-quality/water-withdrawal-registration-program.html"],
    "OK": ["Streams and springs that feed them follow prior appropriation, with permits from the Oklahoma Water Resources Board; "
           "groundwater belongs to the owner of the land above it.", "https://www.oklahoma.gov/owrb/water-permitting.html"],
    "CA": ["California recognizes both riparian and appropriative rights, and springs that feed a stream can be subject to "
           "others' rights downstream. The State Water Board keeps the records.", "https://www.waterboards.ca.gov/waterrights/"],
    "HI": ["Water is held in public trust and its use is regulated by the state Commission on Water Resource Management.",
           "https://dlnr.hawaii.gov/cwrm/"],
    "NV": [APPROP, "https://water.nv.gov/"], "UT": [APPROP, "https://www.waterrights.utah.gov/"],
    "ID": [APPROP, "https://idwr.idaho.gov/"], "OR": [APPROP, "https://www.oregon.gov/owrd/"],
    "MT": [APPROP, "https://dnrc.mt.gov/"], "WA": [APPROP, "https://ecology.wa.gov/"],
    "WY": [APPROP, "https://seo.wyo.gov/"], "CO": [APPROP, "https://dwr.colorado.gov/"],
    "NM": [APPROP, "https://www.ose.nm.gov/"], "AZ": [APPROP, "https://www.azwater.gov/"],
    "SD": [APPROP, "https://danr.sd.gov/"], "ND": [APPROP, "https://www.swc.nd.gov/"],
    "NE": [APPROP, "https://dnr.nebraska.gov/"], "KS": [APPROP, "https://agriculture.ks.gov/"],
    "AK": [APPROP, "https://dnr.alaska.gov/"],
}
def law(st):
    return LAW.get(st, [RIPARIAN, None])
