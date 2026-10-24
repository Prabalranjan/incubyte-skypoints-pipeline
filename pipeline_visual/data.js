window.PIPELINE_DATA = {
  "as_of_date": "2024-06-01",
  "files_summary": [
    {
      "filename": "AUS_members.csv",
      "size_bytes": 215,
      "format": "CSV",
      "content": "Unique ID,Member Name,Tier Type,Date of Birth,Date of Enrollment,Date of Flight\n1,Mike,PLT,NULL,2022-05-11,2022-08-01\n2,Jonnathan,GLD,1997-12-13,2021-13-13,2022-01-05\n3,Cristina,SLV,1998-03-12,2022-03-12,2022-03-20\n",
      "line_count": 4
    },
    {
      "filename": "HD_MEMBERS_20240115.txt",
      "size_bytes": 282,
      "format": "TXT",
      "content": "H|20240115|MEMBERSHIP_FEED\nD|1000000001|Ananya Sharma|2022-01-10|2024-03-01|GLD|Agent Alpha|MH|India|1992-05-14\nD|1000000002|Liam Smith|2021-06-20|2024-05-20|PLT|Agent Beta|NSW|Australia|1988-11-03\nD|1000000003|Jessica Miller|2023-02-15|2024-01-10|SLV|Agent Gamma|CA|USA|1995-08-22\n",
      "line_count": 4
    },
    {
      "filename": "IND_members.csv",
      "size_bytes": 203,
      "format": "CSV",
      "content": "ID,Name,DOB,TierCode,EnrollmentDate,Individual or Corporate,Flight Date\n1,Vikas,12/1/1998,SLV,1/1/2022,I,6/15/2022\n2,Rahul,8/13/1982,GLD,3/5/2022,C,3/10/2022\n3,Sameer,8/13/1952,GLD,2/20/2022,I,2/25/2022\n",
      "line_count": 4
    },
    {
      "filename": "redemptions.json",
      "size_bytes": 421,
      "format": "JSON",
      "content": "{\n  \"member_id\": \"1000000001\",\n  \"feed_date\": \"20240115\",\n  \"redemptions\": [\n    {\n      \"txn_id\": \"RX_20240115_001\",\n      \"txn_date\": \"20240112\",\n      \"partner\": \"Singapore Airlines\",\n      \"miles_redeemed\": 12500,\n      \"status\": \"COMPLETED\"\n    },\n    {\n      \"txn_id\": \"RX_20240115_002\",\n      \"txn_date\": \"20240114\",\n      \"partner\": \"Qantas\",\n      \"miles_redeemed\": 8000,\n      \"status\": \"COMPLETED\"\n    }\n  ]\n}\n",
      "line_count": 20
    },
    {
      "filename": "USA_members.csv",
      "size_bytes": 125,
      "format": "CSV",
      "content": "ID,Name,TierCode,EnrollmentDate,FlightDate\n1,Sam,PLT,6152022,8202022\n2,John,SLV,1052022,1152022\n3,Mike,GLD,12282021,12302021\n",
      "line_count": 4
    }
  ],
  "file_traces": [
    {
      "file_name": "AUS_members.csv",
      "adapter_class": "AusCsvAdapter",
      "adapter_file": "src/skypoints/adapters/csv_adapter.py",
      "raw_records": [
        {
          "source_system": "AUS_CSV",
          "source_file_name": "AUS_members.csv",
          "source_file_timestamp": "2026-10-22T15:44:14.385342+00:00",
          "source_row_number": 1,
          "raw_payload": "Unique ID,Member Name,Tier Type,Date of Birth,Date of Enrollment,Date of Flight"
        },
        {
          "source_system": "AUS_CSV",
          "source_file_name": "AUS_members.csv",
          "source_file_timestamp": "2026-10-22T15:44:14.385342+00:00",
          "source_row_number": 2,
          "raw_payload": "1,Mike,PLT,NULL,2022-05-11,2022-08-01"
        },
        {
          "source_system": "AUS_CSV",
          "source_file_name": "AUS_members.csv",
          "source_file_timestamp": "2026-10-22T15:44:14.385342+00:00",
          "source_row_number": 3,
          "raw_payload": "2,Jonnathan,GLD,1997-12-13,2021-13-13,2022-01-05"
        },
        {
          "source_system": "AUS_CSV",
          "source_file_name": "AUS_members.csv",
          "source_file_timestamp": "2026-10-22T15:44:14.385342+00:00",
          "source_row_number": 4,
          "raw_payload": "3,Cristina,SLV,1998-03-12,2022-03-12,2022-03-20"
        }
      ],
      "parsed_records": [
        {
          "member_id": "1",
          "member_name": "Mike",
          "dob": null,
          "enrollment_date": "2022-05-11",
          "last_flight_date": "2022-08-01",
          "tier_code": "PLT",
          "agent_name": null,
          "state": null,
          "country": "Australia",
          "is_active": "A",
          "source_system": "AUS_CSV",
          "source_file_name": "AUS_members.csv",
          "source_row_number": 2,
          "validation_status": "VALID",
          "validation_reason": null,
          "age": null,
          "stale_member": null
        },
        {
          "member_id": "2",
          "member_name": "Jonnathan",
          "dob": "1997-12-13",
          "enrollment_date": null,
          "last_flight_date": "2022-01-05",
          "tier_code": "GLD",
          "agent_name": null,
          "state": null,
          "country": "Australia",
          "is_active": "A",
          "source_system": "AUS_CSV",
          "source_file_name": "AUS_members.csv",
          "source_row_number": 3,
          "validation_status": "WARNING",
          "validation_reason": "Unparseable Date of Enrollment '2021-13-13'",
          "age": null,
          "stale_member": null
        },
        {
          "member_id": "3",
          "member_name": "Cristina",
          "dob": "1998-03-12",
          "enrollment_date": "2022-03-12",
          "last_flight_date": "2022-03-20",
          "tier_code": "SLV",
          "agent_name": null,
          "state": null,
          "country": "Australia",
          "is_active": "A",
          "source_system": "AUS_CSV",
          "source_file_name": "AUS_members.csv",
          "source_row_number": 4,
          "validation_status": "VALID",
          "validation_reason": null,
          "age": null,
          "stale_member": null
        }
      ]
    },
    {
      "file_name": "HD_MEMBERS_20240115.txt",
      "adapter_class": "HDAdapter",
      "adapter_file": "src/skypoints/adapters/hd_adapter.py",
      "raw_records": [
        {
          "source_system": "HD_FEED",
          "source_file_name": "HD_MEMBERS_20240115.txt",
          "source_file_timestamp": "2024-01-15T00:00:00+00:00",
          "source_row_number": 1,
          "raw_payload": "H|20240115|MEMBERSHIP_FEED"
        },
        {
          "source_system": "HD_FEED",
          "source_file_name": "HD_MEMBERS_20240115.txt",
          "source_file_timestamp": "2024-01-15T00:00:00+00:00",
          "source_row_number": 2,
          "raw_payload": "D|1000000001|Ananya Sharma|2022-01-10|2024-03-01|GLD|Agent Alpha|MH|India|1992-05-14"
        },
        {
          "source_system": "HD_FEED",
          "source_file_name": "HD_MEMBERS_20240115.txt",
          "source_file_timestamp": "2024-01-15T00:00:00+00:00",
          "source_row_number": 3,
          "raw_payload": "D|1000000002|Liam Smith|2021-06-20|2024-05-20|PLT|Agent Beta|NSW|Australia|1988-11-03"
        },
        {
          "source_system": "HD_FEED",
          "source_file_name": "HD_MEMBERS_20240115.txt",
          "source_file_timestamp": "2024-01-15T00:00:00+00:00",
          "source_row_number": 4,
          "raw_payload": "D|1000000003|Jessica Miller|2023-02-15|2024-01-10|SLV|Agent Gamma|CA|USA|1995-08-22"
        }
      ],
      "parsed_records": [
        {
          "member_id": "Ananya Sharma",
          "member_name": "1000000001",
          "dob": null,
          "enrollment_date": null,
          "last_flight_date": null,
          "tier_code": null,
          "agent_name": null,
          "state": null,
          "country": null,
          "is_active": "A",
          "source_system": "HD_FEED",
          "source_file_name": "HD_MEMBERS_20240115.txt",
          "source_row_number": 2,
          "validation_status": "QUARANTINE",
          "validation_reason": "Malformed H/D record: expected 11 fields, got 10",
          "age": null,
          "stale_member": null
        },
        {
          "member_id": "Liam Smith",
          "member_name": "1000000002",
          "dob": null,
          "enrollment_date": null,
          "last_flight_date": null,
          "tier_code": null,
          "agent_name": null,
          "state": null,
          "country": null,
          "is_active": "A",
          "source_system": "HD_FEED",
          "source_file_name": "HD_MEMBERS_20240115.txt",
          "source_row_number": 3,
          "validation_status": "QUARANTINE",
          "validation_reason": "Malformed H/D record: expected 11 fields, got 10",
          "age": null,
          "stale_member": null
        },
        {
          "member_id": "Jessica Miller",
          "member_name": "1000000003",
          "dob": null,
          "enrollment_date": null,
          "last_flight_date": null,
          "tier_code": null,
          "agent_name": null,
          "state": null,
          "country": null,
          "is_active": "A",
          "source_system": "HD_FEED",
          "source_file_name": "HD_MEMBERS_20240115.txt",
          "source_row_number": 4,
          "validation_status": "QUARANTINE",
          "validation_reason": "Malformed H/D record: expected 11 fields, got 10",
          "age": null,
          "stale_member": null
        }
      ]
    },
    {
      "file_name": "IND_members.csv",
      "adapter_class": "IndCsvAdapter",
      "adapter_file": "src/skypoints/adapters/csv_adapter.py",
      "raw_records": [
        {
          "source_system": "IND_CSV",
          "source_file_name": "IND_members.csv",
          "source_file_timestamp": "2026-10-22T15:44:22.267210+00:00",
          "source_row_number": 1,
          "raw_payload": "ID,Name,DOB,TierCode,EnrollmentDate,Individual or Corporate,Flight Date"
        },
        {
          "source_system": "IND_CSV",
          "source_file_name": "IND_members.csv",
          "source_file_timestamp": "2026-10-22T15:44:22.267210+00:00",
          "source_row_number": 2,
          "raw_payload": "1,Vikas,12/1/1998,SLV,1/1/2022,I,6/15/2022"
        },
        {
          "source_system": "IND_CSV",
          "source_file_name": "IND_members.csv",
          "source_file_timestamp": "2026-10-22T15:44:22.267210+00:00",
          "source_row_number": 3,
          "raw_payload": "2,Rahul,8/13/1982,GLD,3/5/2022,C,3/10/2022"
        },
        {
          "source_system": "IND_CSV",
          "source_file_name": "IND_members.csv",
          "source_file_timestamp": "2026-10-22T15:44:22.267210+00:00",
          "source_row_number": 4,
          "raw_payload": "3,Sameer,8/13/1952,GLD,2/20/2022,I,2/25/2022"
        }
      ],
      "parsed_records": [
        {
          "member_id": "1",
          "member_name": "Vikas",
          "dob": "1998-12-01",
          "enrollment_date": "2022-01-01",
          "last_flight_date": "2022-06-15",
          "tier_code": "SLV",
          "agent_name": null,
          "state": null,
          "country": "India",
          "is_active": "A",
          "source_system": "IND_CSV",
          "source_file_name": "IND_members.csv",
          "source_row_number": 2,
          "validation_status": "VALID",
          "validation_reason": null,
          "age": null,
          "stale_member": null
        },
        {
          "member_id": "2",
          "member_name": "Rahul",
          "dob": "1982-08-13",
          "enrollment_date": "2022-03-05",
          "last_flight_date": "2022-03-10",
          "tier_code": "GLD",
          "agent_name": null,
          "state": null,
          "country": "India",
          "is_active": "A",
          "source_system": "IND_CSV",
          "source_file_name": "IND_members.csv",
          "source_row_number": 3,
          "validation_status": "VALID",
          "validation_reason": null,
          "age": null,
          "stale_member": null
        },
        {
          "member_id": "3",
          "member_name": "Sameer",
          "dob": "1952-08-13",
          "enrollment_date": "2022-02-20",
          "last_flight_date": "2022-02-25",
          "tier_code": "GLD",
          "agent_name": null,
          "state": null,
          "country": "India",
          "is_active": "A",
          "source_system": "IND_CSV",
          "source_file_name": "IND_members.csv",
          "source_row_number": 4,
          "validation_status": "VALID",
          "validation_reason": null,
          "age": null,
          "stale_member": null
        }
      ]
    },
    {
      "file_name": "redemptions.json",
      "adapter_class": "JsonRedemptionAdapter",
      "adapter_file": "src/skypoints/adapters/json_adapter.py",
      "raw_records": [
        {
          "source_system": "JSON_REDEMPTION_FEED",
          "source_file_name": "redemptions.json",
          "source_file_timestamp": "2026-10-22T15:44:55.350185+00:00",
          "source_row_number": 1,
          "raw_payload": "{\n  \"member_id\": \"1000000001\",\n  \"feed_date\": \"20240115\",\n  \"redemptions\": [\n    {\n      \"txn_id\": \"RX_20240115_001\",\n      \"txn_date\": \"20240112\",\n      \"partner\": \"Singapore Airlines\",\n      \"miles_redeemed\": 12500,\n      \"status\": \"COMPLETED\"\n    },\n    {\n      \"txn_id\": \"RX_20240115_002\",\n      \"txn_date\": \"20240114\",\n      \"partner\": \"Qantas\",\n      \"miles_redeemed\": 8000,\n      \"status\": \"COMPLETED\"\n    }\n  ]\n}\n"
        }
      ],
      "parsed_records": [
        {
          "txn_id": "RX_20240115_001",
          "member_id": "1000000001",
          "txn_date": "2024-01-12",
          "partner": "Singapore Airlines",
          "miles_redeemed": 12500,
          "status": "COMPLETED",
          "feed_date": "2024-01-15",
          "source_file_name": "redemptions.json"
        },
        {
          "txn_id": "RX_20240115_002",
          "member_id": "1000000001",
          "txn_date": "2024-01-14",
          "partner": "Qantas",
          "miles_redeemed": 8000,
          "status": "COMPLETED",
          "feed_date": "2024-01-15",
          "source_file_name": "redemptions.json"
        }
      ]
    },
    {
      "file_name": "USA_members.csv",
      "adapter_class": "UsaCsvAdapter",
      "adapter_file": "src/skypoints/adapters/csv_adapter.py",
      "raw_records": [
        {
          "source_system": "USA_CSV",
          "source_file_name": "USA_members.csv",
          "source_file_timestamp": "2026-10-22T15:44:28.417275+00:00",
          "source_row_number": 1,
          "raw_payload": "ID,Name,TierCode,EnrollmentDate,FlightDate"
        },
        {
          "source_system": "USA_CSV",
          "source_file_name": "USA_members.csv",
          "source_file_timestamp": "2026-10-22T15:44:28.417275+00:00",
          "source_row_number": 2,
          "raw_payload": "1,Sam,PLT,6152022,8202022"
        },
        {
          "source_system": "USA_CSV",
          "source_file_name": "USA_members.csv",
          "source_file_timestamp": "2026-10-22T15:44:28.417275+00:00",
          "source_row_number": 3,
          "raw_payload": "2,John,SLV,1052022,1152022"
        },
        {
          "source_system": "USA_CSV",
          "source_file_name": "USA_members.csv",
          "source_file_timestamp": "2026-10-22T15:44:28.417275+00:00",
          "source_row_number": 4,
          "raw_payload": "3,Mike,GLD,12282021,12302021"
        }
      ],
      "parsed_records": [
        {
          "member_id": "1",
          "member_name": "Sam",
          "dob": null,
          "enrollment_date": "2022-06-15",
          "last_flight_date": "2022-08-20",
          "tier_code": "PLT",
          "agent_name": null,
          "state": null,
          "country": "USA",
          "is_active": "A",
          "source_system": "USA_CSV",
          "source_file_name": "USA_members.csv",
          "source_row_number": 2,
          "validation_status": "VALID",
          "validation_reason": null,
          "age": null,
          "stale_member": null
        },
        {
          "member_id": "2",
          "member_name": "John",
          "dob": null,
          "enrollment_date": "2022-01-05",
          "last_flight_date": "2022-01-15",
          "tier_code": "SLV",
          "agent_name": null,
          "state": null,
          "country": "USA",
          "is_active": "A",
          "source_system": "USA_CSV",
          "source_file_name": "USA_members.csv",
          "source_row_number": 3,
          "validation_status": "VALID",
          "validation_reason": null,
          "age": null,
          "stale_member": null
        },
        {
          "member_id": "3",
          "member_name": "Mike",
          "dob": null,
          "enrollment_date": "2021-12-28",
          "last_flight_date": "2021-12-30",
          "tier_code": "GLD",
          "agent_name": null,
          "state": null,
          "country": "USA",
          "is_active": "A",
          "source_system": "USA_CSV",
          "source_file_name": "USA_members.csv",
          "source_row_number": 4,
          "validation_status": "VALID",
          "validation_reason": null,
          "age": null,
          "stale_member": null
        }
      ]
    }
  ],
  "bronze_count": 17,
  "silver_count": 9,
  "quarantine_count": 3,
  "bronze_records": [
    {
      "source_system": "AUS_CSV",
      "source_file_name": "AUS_members.csv",
      "source_file_timestamp": "2026-10-22T15:44:14.385342+00:00",
      "source_row_number": 1,
      "raw_payload": "Unique ID,Member Name,Tier Type,Date of Birth,Date of Enrollment,Date of Flight"
    },
    {
      "source_system": "AUS_CSV",
      "source_file_name": "AUS_members.csv",
      "source_file_timestamp": "2026-10-22T15:44:14.385342+00:00",
      "source_row_number": 2,
      "raw_payload": "1,Mike,PLT,NULL,2022-05-11,2022-08-01"
    },
    {
      "source_system": "AUS_CSV",
      "source_file_name": "AUS_members.csv",
      "source_file_timestamp": "2026-10-22T15:44:14.385342+00:00",
      "source_row_number": 3,
      "raw_payload": "2,Jonnathan,GLD,1997-12-13,2021-13-13,2022-01-05"
    },
    {
      "source_system": "AUS_CSV",
      "source_file_name": "AUS_members.csv",
      "source_file_timestamp": "2026-10-22T15:44:14.385342+00:00",
      "source_row_number": 4,
      "raw_payload": "3,Cristina,SLV,1998-03-12,2022-03-12,2022-03-20"
    },
    {
      "source_system": "HD_FEED",
      "source_file_name": "HD_MEMBERS_20240115.txt",
      "source_file_timestamp": "2024-01-15T00:00:00+00:00",
      "source_row_number": 1,
      "raw_payload": "H|20240115|MEMBERSHIP_FEED"
    },
    {
      "source_system": "HD_FEED",
      "source_file_name": "HD_MEMBERS_20240115.txt",
      "source_file_timestamp": "2024-01-15T00:00:00+00:00",
      "source_row_number": 2,
      "raw_payload": "D|1000000001|Ananya Sharma|2022-01-10|2024-03-01|GLD|Agent Alpha|MH|India|1992-05-14"
    },
    {
      "source_system": "HD_FEED",
      "source_file_name": "HD_MEMBERS_20240115.txt",
      "source_file_timestamp": "2024-01-15T00:00:00+00:00",
      "source_row_number": 3,
      "raw_payload": "D|1000000002|Liam Smith|2021-06-20|2024-05-20|PLT|Agent Beta|NSW|Australia|1988-11-03"
    },
    {
      "source_system": "HD_FEED",
      "source_file_name": "HD_MEMBERS_20240115.txt",
      "source_file_timestamp": "2024-01-15T00:00:00+00:00",
      "source_row_number": 4,
      "raw_payload": "D|1000000003|Jessica Miller|2023-02-15|2024-01-10|SLV|Agent Gamma|CA|USA|1995-08-22"
    },
    {
      "source_system": "IND_CSV",
      "source_file_name": "IND_members.csv",
      "source_file_timestamp": "2026-10-22T15:44:22.267210+00:00",
      "source_row_number": 1,
      "raw_payload": "ID,Name,DOB,TierCode,EnrollmentDate,Individual or Corporate,Flight Date"
    },
    {
      "source_system": "IND_CSV",
      "source_file_name": "IND_members.csv",
      "source_file_timestamp": "2026-10-22T15:44:22.267210+00:00",
      "source_row_number": 2,
      "raw_payload": "1,Vikas,12/1/1998,SLV,1/1/2022,I,6/15/2022"
    },
    {
      "source_system": "IND_CSV",
      "source_file_name": "IND_members.csv",
      "source_file_timestamp": "2026-10-22T15:44:22.267210+00:00",
      "source_row_number": 3,
      "raw_payload": "2,Rahul,8/13/1982,GLD,3/5/2022,C,3/10/2022"
    },
    {
      "source_system": "IND_CSV",
      "source_file_name": "IND_members.csv",
      "source_file_timestamp": "2026-10-22T15:44:22.267210+00:00",
      "source_row_number": 4,
      "raw_payload": "3,Sameer,8/13/1952,GLD,2/20/2022,I,2/25/2022"
    },
    {
      "source_system": "JSON_REDEMPTION_FEED",
      "source_file_name": "redemptions.json",
      "source_file_timestamp": "2026-10-22T15:44:55.350185+00:00",
      "source_row_number": 1,
      "raw_payload": "{\n  \"member_id\": \"1000000001\",\n  \"feed_date\": \"20240115\",\n  \"redemptions\": [\n    {\n      \"txn_id\": \"RX_20240115_001\",\n      \"txn_date\": \"20240112\",\n      \"partner\": \"Singapore Airlines\",\n      \"miles_redeemed\": 12500,\n      \"status\": \"COMPLETED\"\n    },\n    {\n      \"txn_id\": \"RX_20240115_002\",\n      \"txn_date\": \"20240114\",\n      \"partner\": \"Qantas\",\n      \"miles_redeemed\": 8000,\n      \"status\": \"COMPLETED\"\n    }\n  ]\n}\n"
    },
    {
      "source_system": "USA_CSV",
      "source_file_name": "USA_members.csv",
      "source_file_timestamp": "2026-10-22T15:44:28.417275+00:00",
      "source_row_number": 1,
      "raw_payload": "ID,Name,TierCode,EnrollmentDate,FlightDate"
    },
    {
      "source_system": "USA_CSV",
      "source_file_name": "USA_members.csv",
      "source_file_timestamp": "2026-10-22T15:44:28.417275+00:00",
      "source_row_number": 2,
      "raw_payload": "1,Sam,PLT,6152022,8202022"
    },
    {
      "source_system": "USA_CSV",
      "source_file_name": "USA_members.csv",
      "source_file_timestamp": "2026-10-22T15:44:28.417275+00:00",
      "source_row_number": 3,
      "raw_payload": "2,John,SLV,1052022,1152022"
    },
    {
      "source_system": "USA_CSV",
      "source_file_name": "USA_members.csv",
      "source_file_timestamp": "2026-10-22T15:44:28.417275+00:00",
      "source_row_number": 4,
      "raw_payload": "3,Mike,GLD,12282021,12302021"
    }
  ],
  "silver_enriched": [
    {
      "member_id": "1",
      "member_name": "Mike",
      "country": "Australia",
      "dob": null,
      "last_flight_date": "2022-08-01",
      "age": null,
      "stale_member": true,
      "validation_status": "VALID",
      "validation_reason": null,
      "source_file_name": "AUS_members.csv",
      "source_row_number": 2
    },
    {
      "member_id": "2",
      "member_name": "Jonnathan",
      "country": "Australia",
      "dob": "1997-12-13",
      "last_flight_date": "2022-01-05",
      "age": 26,
      "stale_member": true,
      "validation_status": "WARNING",
      "validation_reason": "Unparseable Date of Enrollment '2021-13-13'",
      "source_file_name": "AUS_members.csv",
      "source_row_number": 3
    },
    {
      "member_id": "3",
      "member_name": "Cristina",
      "country": "Australia",
      "dob": "1998-03-12",
      "last_flight_date": "2022-03-20",
      "age": 26,
      "stale_member": true,
      "validation_status": "VALID",
      "validation_reason": null,
      "source_file_name": "AUS_members.csv",
      "source_row_number": 4
    },
    {
      "member_id": "1",
      "member_name": "Vikas",
      "country": "India",
      "dob": "1998-12-01",
      "last_flight_date": "2022-06-15",
      "age": 25,
      "stale_member": true,
      "validation_status": "VALID",
      "validation_reason": null,
      "source_file_name": "IND_members.csv",
      "source_row_number": 2
    },
    {
      "member_id": "2",
      "member_name": "Rahul",
      "country": "India",
      "dob": "1982-08-13",
      "last_flight_date": "2022-03-10",
      "age": 41,
      "stale_member": true,
      "validation_status": "VALID",
      "validation_reason": null,
      "source_file_name": "IND_members.csv",
      "source_row_number": 3
    },
    {
      "member_id": "3",
      "member_name": "Sameer",
      "country": "India",
      "dob": "1952-08-13",
      "last_flight_date": "2022-02-25",
      "age": 71,
      "stale_member": true,
      "validation_status": "VALID",
      "validation_reason": null,
      "source_file_name": "IND_members.csv",
      "source_row_number": 4
    },
    {
      "member_id": "1",
      "member_name": "Sam",
      "country": "USA",
      "dob": null,
      "last_flight_date": "2022-08-20",
      "age": null,
      "stale_member": true,
      "validation_status": "VALID",
      "validation_reason": null,
      "source_file_name": "USA_members.csv",
      "source_row_number": 2
    },
    {
      "member_id": "2",
      "member_name": "John",
      "country": "USA",
      "dob": null,
      "last_flight_date": "2022-01-15",
      "age": null,
      "stale_member": true,
      "validation_status": "VALID",
      "validation_reason": null,
      "source_file_name": "USA_members.csv",
      "source_row_number": 3
    },
    {
      "member_id": "3",
      "member_name": "Mike",
      "country": "USA",
      "dob": null,
      "last_flight_date": "2021-12-30",
      "age": null,
      "stale_member": true,
      "validation_status": "VALID",
      "validation_reason": null,
      "source_file_name": "USA_members.csv",
      "source_row_number": 4
    }
  ],
  "quarantine_records": [
    {
      "member_id": "Ananya Sharma",
      "member_name": "1000000001",
      "reason": "Malformed H/D record: expected 11 fields, got 10",
      "source_file": "HD_MEMBERS_20240115.txt",
      "row": 2
    },
    {
      "member_id": "Liam Smith",
      "member_name": "1000000002",
      "reason": "Malformed H/D record: expected 11 fields, got 10",
      "source_file": "HD_MEMBERS_20240115.txt",
      "row": 3
    },
    {
      "member_id": "Jessica Miller",
      "member_name": "1000000003",
      "reason": "Malformed H/D record: expected 11 fields, got 10",
      "source_file": "HD_MEMBERS_20240115.txt",
      "row": 4
    }
  ],
  "country_tables": {
    "Table_Australia": [
      {
        "member_id": "1",
        "member_name": "Mike",
        "enrollment_date": "2022-05-11",
        "last_flight_date": "2022-08-01",
        "tier_code": "PLT",
        "agent_name": null,
        "state": null,
        "country": "Australia",
        "post_code": null,
        "dob": null,
        "is_active": "A",
        "age": null,
        "stale_member": true,
        "source_system": "AUS_CSV",
        "source_file_name": "AUS_members.csv",
        "source_file_timestamp": "2026-10-22T21:14:14.385342",
        "source_row_number": 2,
        "ingested_at": "2026-10-24T19:58:36.241941",
        "validation_status": "VALID"
      },
      {
        "member_id": "2",
        "member_name": "Jonnathan",
        "enrollment_date": null,
        "last_flight_date": "2022-01-05",
        "tier_code": "GLD",
        "agent_name": null,
        "state": null,
        "country": "Australia",
        "post_code": null,
        "dob": "1997-12-13",
        "is_active": "A",
        "age": 26,
        "stale_member": true,
        "source_system": "AUS_CSV",
        "source_file_name": "AUS_members.csv",
        "source_file_timestamp": "2026-10-22T21:14:14.385342",
        "source_row_number": 3,
        "ingested_at": "2026-10-24T19:58:36.242687",
        "validation_status": "WARNING"
      },
      {
        "member_id": "3",
        "member_name": "Cristina",
        "enrollment_date": "2022-03-12",
        "last_flight_date": "2022-03-20",
        "tier_code": "SLV",
        "agent_name": null,
        "state": null,
        "country": "Australia",
        "post_code": null,
        "dob": "1998-03-12",
        "is_active": "A",
        "age": 26,
        "stale_member": true,
        "source_system": "AUS_CSV",
        "source_file_name": "AUS_members.csv",
        "source_file_timestamp": "2026-10-22T21:14:14.385342",
        "source_row_number": 4,
        "ingested_at": "2026-10-24T19:58:36.242724",
        "validation_status": "VALID"
      }
    ],
    "Table_India": [
      {
        "member_id": "1",
        "member_name": "Vikas",
        "enrollment_date": "2022-01-01",
        "last_flight_date": "2022-06-15",
        "tier_code": "SLV",
        "agent_name": null,
        "state": null,
        "country": "India",
        "post_code": null,
        "dob": "1998-12-01",
        "is_active": "A",
        "age": 25,
        "stale_member": true,
        "source_system": "IND_CSV",
        "source_file_name": "IND_members.csv",
        "source_file_timestamp": "2026-10-22T21:14:22.267210",
        "source_row_number": 2,
        "ingested_at": "2026-10-24T19:58:36.243372",
        "validation_status": "VALID"
      },
      {
        "member_id": "2",
        "member_name": "Rahul",
        "enrollment_date": "2022-03-05",
        "last_flight_date": "2022-03-10",
        "tier_code": "GLD",
        "agent_name": null,
        "state": null,
        "country": "India",
        "post_code": null,
        "dob": "1982-08-13",
        "is_active": "A",
        "age": 41,
        "stale_member": true,
        "source_system": "IND_CSV",
        "source_file_name": "IND_members.csv",
        "source_file_timestamp": "2026-10-22T21:14:22.267210",
        "source_row_number": 3,
        "ingested_at": "2026-10-24T19:58:36.243423",
        "validation_status": "VALID"
      },
      {
        "member_id": "3",
        "member_name": "Sameer",
        "enrollment_date": "2022-02-20",
        "last_flight_date": "2022-02-25",
        "tier_code": "GLD",
        "agent_name": null,
        "state": null,
        "country": "India",
        "post_code": null,
        "dob": "1952-08-13",
        "is_active": "A",
        "age": 71,
        "stale_member": true,
        "source_system": "IND_CSV",
        "source_file_name": "IND_members.csv",
        "source_file_timestamp": "2026-10-22T21:14:22.267210",
        "source_row_number": 4,
        "ingested_at": "2026-10-24T19:58:36.243472",
        "validation_status": "VALID"
      }
    ],
    "Table_USA": [
      {
        "member_id": "1",
        "member_name": "Sam",
        "enrollment_date": "2022-06-15",
        "last_flight_date": "2022-08-20",
        "tier_code": "PLT",
        "agent_name": null,
        "state": null,
        "country": "USA",
        "post_code": null,
        "dob": null,
        "is_active": "A",
        "age": null,
        "stale_member": true,
        "source_system": "USA_CSV",
        "source_file_name": "USA_members.csv",
        "source_file_timestamp": "2026-10-22T21:14:28.417275",
        "source_row_number": 2,
        "ingested_at": "2026-10-24T19:58:36.244007",
        "validation_status": "VALID"
      },
      {
        "member_id": "2",
        "member_name": "John",
        "enrollment_date": "2022-01-05",
        "last_flight_date": "2022-01-15",
        "tier_code": "SLV",
        "agent_name": null,
        "state": null,
        "country": "USA",
        "post_code": null,
        "dob": null,
        "is_active": "A",
        "age": null,
        "stale_member": true,
        "source_system": "USA_CSV",
        "source_file_name": "USA_members.csv",
        "source_file_timestamp": "2026-10-22T21:14:28.417275",
        "source_row_number": 3,
        "ingested_at": "2026-10-24T19:58:36.244029",
        "validation_status": "VALID"
      },
      {
        "member_id": "3",
        "member_name": "Mike",
        "enrollment_date": "2021-12-28",
        "last_flight_date": "2021-12-30",
        "tier_code": "GLD",
        "agent_name": null,
        "state": null,
        "country": "USA",
        "post_code": null,
        "dob": null,
        "is_active": "A",
        "age": null,
        "stale_member": true,
        "source_system": "USA_CSV",
        "source_file_name": "USA_members.csv",
        "source_file_timestamp": "2026-10-22T21:14:28.417275",
        "source_row_number": 4,
        "ingested_at": "2026-10-24T19:58:36.244039",
        "validation_status": "VALID"
      }
    ]
  },
  "current_profiles": [
    {
      "member_id": "1",
      "member_name": "Vikas",
      "enrollment_date": "2022-01-01",
      "last_flight_date": "2022-06-15",
      "tier_code": "SLV",
      "agent_name": null,
      "state": null,
      "country": "India",
      "post_code": null,
      "dob": "1998-12-01",
      "is_active": "A",
      "age": 25,
      "stale_member": true,
      "source_system": "IND_CSV",
      "source_file_name": "IND_members.csv",
      "source_file_timestamp": "2026-10-22T21:14:22.267210",
      "source_row_number": 2,
      "ingested_at": "2026-10-24T19:58:36.243372",
      "validation_status": "VALID"
    },
    {
      "member_id": "1",
      "member_name": "Sam",
      "enrollment_date": "2022-06-15",
      "last_flight_date": "2022-08-20",
      "tier_code": "PLT",
      "agent_name": null,
      "state": null,
      "country": "USA",
      "post_code": null,
      "dob": null,
      "is_active": "A",
      "age": null,
      "stale_member": true,
      "source_system": "USA_CSV",
      "source_file_name": "USA_members.csv",
      "source_file_timestamp": "2026-10-22T21:14:28.417275",
      "source_row_number": 2,
      "ingested_at": "2026-10-24T19:58:36.244007",
      "validation_status": "VALID"
    },
    {
      "member_id": "1",
      "member_name": "Mike",
      "enrollment_date": "2022-05-11",
      "last_flight_date": "2022-08-01",
      "tier_code": "PLT",
      "agent_name": null,
      "state": null,
      "country": "Australia",
      "post_code": null,
      "dob": null,
      "is_active": "A",
      "age": null,
      "stale_member": true,
      "source_system": "AUS_CSV",
      "source_file_name": "AUS_members.csv",
      "source_file_timestamp": "2026-10-22T21:14:14.385342",
      "source_row_number": 2,
      "ingested_at": "2026-10-24T19:58:36.241941",
      "validation_status": "VALID"
    },
    {
      "member_id": "2",
      "member_name": "Rahul",
      "enrollment_date": "2022-03-05",
      "last_flight_date": "2022-03-10",
      "tier_code": "GLD",
      "agent_name": null,
      "state": null,
      "country": "India",
      "post_code": null,
      "dob": "1982-08-13",
      "is_active": "A",
      "age": 41,
      "stale_member": true,
      "source_system": "IND_CSV",
      "source_file_name": "IND_members.csv",
      "source_file_timestamp": "2026-10-22T21:14:22.267210",
      "source_row_number": 3,
      "ingested_at": "2026-10-24T19:58:36.243423",
      "validation_status": "VALID"
    },
    {
      "member_id": "2",
      "member_name": "John",
      "enrollment_date": "2022-01-05",
      "last_flight_date": "2022-01-15",
      "tier_code": "SLV",
      "agent_name": null,
      "state": null,
      "country": "USA",
      "post_code": null,
      "dob": null,
      "is_active": "A",
      "age": null,
      "stale_member": true,
      "source_system": "USA_CSV",
      "source_file_name": "USA_members.csv",
      "source_file_timestamp": "2026-10-22T21:14:28.417275",
      "source_row_number": 3,
      "ingested_at": "2026-10-24T19:58:36.244029",
      "validation_status": "VALID"
    },
    {
      "member_id": "2",
      "member_name": "Jonnathan",
      "enrollment_date": null,
      "last_flight_date": "2022-01-05",
      "tier_code": "GLD",
      "agent_name": null,
      "state": null,
      "country": "Australia",
      "post_code": null,
      "dob": "1997-12-13",
      "is_active": "A",
      "age": 26,
      "stale_member": true,
      "source_system": "AUS_CSV",
      "source_file_name": "AUS_members.csv",
      "source_file_timestamp": "2026-10-22T21:14:14.385342",
      "source_row_number": 3,
      "ingested_at": "2026-10-24T19:58:36.242687",
      "validation_status": "WARNING"
    },
    {
      "member_id": "3",
      "member_name": "Sameer",
      "enrollment_date": "2022-02-20",
      "last_flight_date": "2022-02-25",
      "tier_code": "GLD",
      "agent_name": null,
      "state": null,
      "country": "India",
      "post_code": null,
      "dob": "1952-08-13",
      "is_active": "A",
      "age": 71,
      "stale_member": true,
      "source_system": "IND_CSV",
      "source_file_name": "IND_members.csv",
      "source_file_timestamp": "2026-10-22T21:14:22.267210",
      "source_row_number": 4,
      "ingested_at": "2026-10-24T19:58:36.243472",
      "validation_status": "VALID"
    },
    {
      "member_id": "3",
      "member_name": "Mike",
      "enrollment_date": "2021-12-28",
      "last_flight_date": "2021-12-30",
      "tier_code": "GLD",
      "agent_name": null,
      "state": null,
      "country": "USA",
      "post_code": null,
      "dob": null,
      "is_active": "A",
      "age": null,
      "stale_member": true,
      "source_system": "USA_CSV",
      "source_file_name": "USA_members.csv",
      "source_file_timestamp": "2026-10-22T21:14:28.417275",
      "source_row_number": 4,
      "ingested_at": "2026-10-24T19:58:36.244039",
      "validation_status": "VALID"
    },
    {
      "member_id": "3",
      "member_name": "Cristina",
      "enrollment_date": "2022-03-12",
      "last_flight_date": "2022-03-20",
      "tier_code": "SLV",
      "agent_name": null,
      "state": null,
      "country": "Australia",
      "post_code": null,
      "dob": "1998-03-12",
      "is_active": "A",
      "age": 26,
      "stale_member": true,
      "source_system": "AUS_CSV",
      "source_file_name": "AUS_members.csv",
      "source_file_timestamp": "2026-10-22T21:14:14.385342",
      "source_row_number": 4,
      "ingested_at": "2026-10-24T19:58:36.242724",
      "validation_status": "VALID"
    }
  ],
  "redemptions": [
    {
      "txn_id": "RX_20240115_001",
      "member_id": "1000000001",
      "feed_date": "2024-01-15",
      "txn_date": "2024-01-12",
      "partner": "Singapore Airlines",
      "miles_redeemed": 12500,
      "status": "COMPLETED",
      "source_file_name": "redemptions.json",
      "source_file_timestamp": "2026-10-22T21:14:55.350185",
      "ingested_at": "2026-10-24T19:58:36.243757",
      "validation_status": "VALID",
      "validation_reason": null
    },
    {
      "txn_id": "RX_20240115_002",
      "member_id": "1000000001",
      "feed_date": "2024-01-15",
      "txn_date": "2024-01-14",
      "partner": "Qantas",
      "miles_redeemed": 8000,
      "status": "COMPLETED",
      "source_file_name": "redemptions.json",
      "source_file_timestamp": "2026-10-22T21:14:55.350185",
      "ingested_at": "2026-10-24T19:58:36.243774",
      "validation_status": "VALID",
      "validation_reason": null
    }
  ],
  "joined_transactions": [
    {
      "txn_id": "RX_20240115_001",
      "txn_date": "2024-01-12T00:00:00",
      "feed_date": "2024-01-15T00:00:00",
      "partner": "Singapore Airlines",
      "miles_redeemed": 12500,
      "txn_status": "COMPLETED",
      "member_id": "1000000001",
      "member_name": null,
      "tier_code": null,
      "country": null,
      "match_status": "UNMATCHED_MEMBER"
    },
    {
      "txn_id": "RX_20240115_002",
      "txn_date": "2024-01-14T00:00:00",
      "feed_date": "2024-01-15T00:00:00",
      "partner": "Qantas",
      "miles_redeemed": 8000,
      "txn_status": "COMPLETED",
      "member_id": "1000000001",
      "member_name": null,
      "tier_code": null,
      "country": null,
      "match_status": "UNMATCHED_MEMBER"
    }
  ],
  "routing_summary": {
    "total_processed": 9,
    "inserted": 9,
    "updated": 0,
    "skipped_late": 0,
    "moved": 0,
    "quarantined": 0,
    "routed_tables": [
      "Table_USA",
      "Table_Australia",
      "Table_India"
    ]
  },
  "scenarios": {
    "age_boundary": [
      {
        "desc": "Day before 30th birthday",
        "as_of": "2024-06-14",
        "dob": "1994-06-15",
        "age": 29
      },
      {
        "desc": "Exact 30th birthday",
        "as_of": "2024-06-15",
        "dob": "1994-06-15",
        "age": 30
      },
      {
        "desc": "Day after 30th birthday",
        "as_of": "2024-06-16",
        "dob": "1994-06-15",
        "age": 30
      },
      {
        "desc": "Leap day baby (2000-02-29) in 2023 (non-leap)",
        "as_of": "2023-02-28",
        "dob": "2000-02-29",
        "age": 22
      },
      {
        "desc": "Leap day baby (2000-02-29) in 2024 (leap year)",
        "as_of": "2024-02-29",
        "dob": "2000-02-29",
        "age": 24
      }
    ],
    "stale_boundary": [
      {
        "desc": "89 days since flight",
        "flight_date": "2024-03-04",
        "days_diff": 89,
        "is_stale": false,
        "status": "ACTIVE"
      },
      {
        "desc": "90 days since flight (Exact boundary)",
        "flight_date": "2024-03-03",
        "days_diff": 90,
        "is_stale": false,
        "status": "ACTIVE (Not Stale)"
      },
      {
        "desc": "91 days since flight (> 90 days)",
        "flight_date": "2024-03-02",
        "days_diff": 91,
        "is_stale": true,
        "status": "STALE"
      },
      {
        "desc": "No flight record (NULL)",
        "flight_date": null,
        "days_diff": null,
        "is_stale": null,
        "status": "UNKNOWN (NULL)"
      }
    ],
    "country_move": {
      "scenario": "Member relocates from India to Australia across consecutive day feeds",
      "step_1": {
        "title": "Day 1 Feed arrives (Member registered in India)",
        "file": "HD_FEED_20240110.txt",
        "member_id": "MOVE_MEMBER_777",
        "country": "India",
        "status": "Active ('A') in Table_India"
      },
      "step_2": {
        "title": "Day 2 Feed arrives (Member moves to Australia)",
        "file": "HD_FEED_20240115.txt",
        "member_id": "MOVE_MEMBER_777",
        "country": "Australia",
        "status": "Active ('A') in Table_Australia, Inactive ('I') in Table_India"
      },
      "guarantee": "Exactly 1 active profile across all country tables in Current_Member_Profiles"
    },
    "late_arrival": {
      "scenario": "Day 1 older file arrives AFTER Day 2 newer file has already updated the profile",
      "day_2_file": {
        "name": "FEED_20240115.txt",
        "tier": "PLT",
        "state": "Applied to Table_USA (Platinum)"
      },
      "day_1_file_late": {
        "name": "FEED_20240110.txt",
        "tier": "SLV",
        "action": "PROTECTED / SKIPPED",
        "reason": "Incoming timestamp (2024-01-10) is older than existing record (2024-01-15)"
      },
      "result_tier": "PLT (Current profile DID NOT regress to Silver)"
    }
  },
  "code_map": [
    {
      "layer": "Layer 1: Bronze (Raw Landing)",
      "purpose": "Verbatim capture of raw payloads with ingestion audit lineage (file name, file timestamp, line number, ingested_at). Zero data loss guarantee.",
      "components": [
        {
          "name": "BaseAdapter",
          "file": "src/skypoints/adapters/base.py",
          "lines": "1-80",
          "desc": "Standardizes parsing contract, extracts file timestamps from naming conventions."
        },
        {
          "name": "HDAdapter",
          "file": "src/skypoints/adapters/hd_adapter.py",
          "lines": "1-169",
          "desc": "Parses pipe-delimited H/D feeds, captures RawRecord, skips headers, handles data quirks."
        },
        {
          "name": "CsvAdapters (Aus, Ind, Usa)",
          "file": "src/skypoints/adapters/csv_adapter.py",
          "lines": "1-346",
          "desc": "Isolates country-specific CSV formats (compact USA dates, Indian M/D/YYYY, Australian NULLs)."
        },
        {
          "name": "RawRecord Model",
          "file": "src/skypoints/models/canonical.py",
          "lines": "12-30",
          "desc": "Immutable data model representing Bronze audit record."
        },
        {
          "name": "raw_landing_feed Table",
          "file": "src/skypoints/storage/database.py",
          "lines": "93-110",
          "desc": "DuckDB storage for Bronze tier."
        }
      ]
    },
    {
      "layer": "Layer 2: Silver (Staging & Data Quality)",
      "purpose": "Standardizes dates, normalizes member identifiers, validates mandatory fields, quarantines corrupted records, and calculates derived columns.",
      "components": [
        {
          "name": "MemberRecord Canonical Model",
          "file": "src/skypoints/models/canonical.py",
          "lines": "32-78",
          "desc": "Canonical schema preserving string member IDs (prevents leading zeros loss)."
        },
        {
          "name": "Enrichment Engine",
          "file": "src/skypoints/enrichment/derived_columns.py",
          "lines": "12-75",
          "desc": "Calculates Age (anniversary boundary + leap year safe) & Stale_Member (> 90 days)."
        },
        {
          "name": "staging_members Table",
          "file": "src/skypoints/storage/database.py",
          "lines": "120-145",
          "desc": "Audit staging table capturing all parsed members."
        },
        {
          "name": "quarantine_members Table",
          "file": "src/skypoints/storage/database.py",
          "lines": "120-145",
          "desc": "Quarantine table preventing invalid/corrupted records from polluting Gold."
        }
      ]
    },
    {
      "layer": "Layer 3: Gold (Country Tables & Target Resolution)",
      "purpose": "Dynamically partitions members into Table_<Country> tables, resolves out-of-order deliveries (late files), handles cross-table country moves, and maintains unified view.",
      "components": [
        {
          "name": "CountryRouter",
          "file": "src/skypoints/router/table_router.py",
          "lines": "18-135",
          "desc": "Deduplication tie-breaker, late-arriving file protection, cross-table country moves."
        },
        {
          "name": "Dynamic Table Creator",
          "file": "src/skypoints/storage/database.py",
          "lines": "50-90",
          "desc": "Safe SQL injection-free DDL generating Table_<Country> dynamically."
        },
        {
          "name": "Current_Member_Profiles View",
          "file": "src/skypoints/router/table_router.py",
          "lines": "180-210",
          "desc": "Dynamic UNION ALL view over all active country records for downstream joins."
        }
      ]
    },
    {
      "layer": "Layer 4: Gold Transactions (Redemptions Feed & Join)",
      "purpose": "Parses nested JSON feeds, unnests arrays into flat transaction records, enforces idempotency on replay, and joins transactions with unified member profiles.",
      "components": [
        {
          "name": "JsonRedemptionAdapter",
          "file": "src/skypoints/adapters/json_adapter.py",
          "lines": "16-165",
          "desc": "Unpacks JSON/NDJSON arrays, standardizes dates, deduplicates on txn_id."
        },
        {
          "name": "Table_Redemptions",
          "file": "src/skypoints/storage/database.py",
          "lines": "75-90",
          "desc": "Primary-keyed transaction table with idempotency."
        },
        {
          "name": "Profile Join Query",
          "file": "src/skypoints/adapters/json_adapter.py",
          "lines": "140-165",
          "desc": "LEFT JOIN against Current_Member_Profiles tagging MATCHED vs UNMATCHED_MEMBER."
        }
      ]
    }
  ]
};
