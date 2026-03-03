#![allow(unexpected_cfgs)]

#[cfg(target_os = "macos")]
use {
    block::ConcreteBlock,
    objc::runtime::{Object, BOOL, YES},
    objc::{class, msg_send, sel, sel_impl},
    std::{
        ffi::{CStr, CString},
        os::raw::c_char,
        ptr,
        sync::{Arc, Condvar, Mutex},
    },
};

use serde::Serialize;
use std::path::{Path, PathBuf};

#[cfg(target_os = "macos")]
const CN_ENTITY_TYPE_CONTACTS: i64 = 0;
#[cfg(target_os = "macos")]
const CN_AUTH_STATUS_NOT_DETERMINED: i64 = 0;
#[cfg(target_os = "macos")]
const CN_AUTH_STATUS_AUTHORIZED: i64 = 3;

#[cfg(target_os = "macos")]
#[link(name = "Contacts", kind = "framework")]
extern "C" {}

#[cfg(target_os = "macos")]
#[link(name = "Foundation", kind = "framework")]
extern "C" {}

#[cfg(target_os = "macos")]
struct ObjcOwned(*mut Object);

#[derive(Clone, Serialize)]
struct Contact {
    id: String,
    #[serde(rename = "firstName", skip_serializing_if = "Option::is_none")]
    first_name: Option<String>,
    #[serde(rename = "lastName", skip_serializing_if = "Option::is_none")]
    last_name: Option<String>,
    #[serde(rename = "companyName", skip_serializing_if = "Option::is_none")]
    company_name: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    phone: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    email: Option<String>,
}

#[cfg(target_os = "macos")]
impl ObjcOwned {
    #[inline]
    fn as_ptr(&self) -> *mut Object {
        self.0
    }
}

#[cfg(target_os = "macos")]
impl Drop for ObjcOwned {
    fn drop(&mut self) {
        unsafe {
            if !self.0.is_null() {
                let _: () = msg_send![self.0, release];
            }
        }
    }
}

#[tauri::command]
async fn get_contacts() -> Result<Vec<Contact>, String> {
    #[cfg(target_os = "macos")]
    {
        tauri::async_runtime::spawn_blocking(move || fetch_contacts())
            .await
            .map_err(|err| err.to_string())?
    }

    #[cfg(not(target_os = "macos"))]
    {
        Err("Contacts are only available on macOS.".into())
    }
}

#[cfg(target_os = "macos")]
fn fetch_contacts() -> Result<Vec<Contact>, String> {
    unsafe {
        let store_ptr: *mut Object = msg_send![class!(CNContactStore), new];
        if store_ptr.is_null() {
            return Err("Failed to create CNContactStore.".into());
        }
        let store = ObjcOwned(store_ptr);
        let store_raw = store.as_ptr();

        ensure_contacts_access(store_raw)?;

        let key_strings = [
            "identifier",
            "givenName",
            "familyName",
            "organizationName",
            "phoneNumbers",
            "emailAddresses",
        ];
        let mut c_strings = Vec::with_capacity(key_strings.len());
        let mut ns_keys = Vec::with_capacity(key_strings.len());
        for key in key_strings {
            let c_string = CString::new(key).map_err(|_| format!("Invalid key: {key}"))?;
            let ns_key: *mut Object =
                msg_send![class!(NSString), stringWithUTF8String: c_string.as_ptr()];
            if ns_key.is_null() {
                return Err(format!("Failed to create NSString for {key}."));
            }
            c_strings.push(c_string);
            ns_keys.push(ns_key);
        }

        let keys_array: *mut Object =
            msg_send![class!(NSArray), arrayWithObjects: ns_keys.as_ptr() count: ns_keys.len()];
        if keys_array.is_null() {
            return Err("Failed to create fetch request keys.".into());
        }

        let request_alloc: *mut Object = msg_send![class!(CNContactFetchRequest), alloc];
        if request_alloc.is_null() {
            return Err("Failed to allocate CNContactFetchRequest.".into());
        }
        let request_ptr: *mut Object = msg_send![request_alloc, initWithKeysToFetch: keys_array];
        if request_ptr.is_null() {
            let _: () = msg_send![request_alloc, release];
            return Err("Failed to initialize CNContactFetchRequest.".into());
        }
        let request = ObjcOwned(request_ptr);
        let request_raw = request.as_ptr();

        let contacts = Arc::new(Mutex::new(Vec::<Contact>::new()));
        let contacts_clone = Arc::clone(&contacts);

        let block = ConcreteBlock::new(move |contact: *mut Object, _stop: *mut BOOL| {
            if let Some(contact_entry) = contact_from_objc(contact) {
                if let Ok(mut list) = contacts_clone.lock() {
                    if !list.iter().any(|existing| existing.id == contact_entry.id) {
                        list.push(contact_entry);
                    }
                }
            }
        });
        let block = block.copy();

        let mut error: *mut Object = ptr::null_mut();
        let success: BOOL = msg_send![store_raw,
            enumerateContactsWithFetchRequest: request_raw
            error: &mut error
            usingBlock: &*block
        ];

        if success != YES {
            if !error.is_null() {
                return Err(ns_error_to_string(error));
            } else {
                return Err("Failed to enumerate contacts.".into());
            }
        }

        let mut result = contacts
            .lock()
            .map_err(|_| "Failed to read contacts list.".to_string())?
            .clone();
        result.sort_by_key(contact_sort_key);
        Ok(result)
    }
}

#[cfg(target_os = "macos")]
fn ensure_contacts_access(store: *mut Object) -> Result<(), String> {
    unsafe {
        let status: i64 = msg_send![class!(CNContactStore), authorizationStatusForEntityType: CN_ENTITY_TYPE_CONTACTS];
        if status == CN_AUTH_STATUS_AUTHORIZED {
            return Ok(());
        }

        if status != CN_AUTH_STATUS_NOT_DETERMINED {
            return Err("Contacts access is not authorized for this app.".into());
        }

        let state = Arc::new((Mutex::new(None::<(bool, Option<String>)>), Condvar::new()));
        let state_clone = Arc::clone(&state);

        let completion = ConcreteBlock::new(move |granted: BOOL, error: *mut Object| {
            let error_message = if error.is_null() {
                None
            } else {
                Some(ns_error_to_string(error))
            };

            let mut guard = state_clone
                .0
                .lock()
                .expect("poisoned contacts access mutex");
            *guard = Some((granted == YES, error_message));
            state_clone.1.notify_one();
        });
        let completion = completion.copy();

        let _: () = msg_send![store, requestAccessForEntityType: CN_ENTITY_TYPE_CONTACTS completionHandler: &*completion];

        let mut guard = state
            .0
            .lock()
            .map_err(|_| "Failed to request contacts access.".to_string())?;
        while guard.is_none() {
            guard = state
                .1
                .wait(guard)
                .map_err(|_| "Failed while waiting for contacts access.".to_string())?;
        }

        if let Some((granted, error_message)) = guard.take() {
            if granted {
                Ok(())
            } else {
                Err(error_message.unwrap_or_else(|| "Contacts access was not granted.".into()))
            }
        } else {
            Err("Contacts access request returned no result.".into())
        }
    }
}

#[cfg(target_os = "macos")]
fn contact_sort_key(contact: &Contact) -> String {
    let first_name = contact.first_name.clone().unwrap_or_default();
    let last_name = contact.last_name.clone().unwrap_or_default();
    let company_name = contact.company_name.clone().unwrap_or_default();
    format!(
        "{}|{}|{}|{}",
        first_name.to_lowercase(),
        last_name.to_lowercase(),
        company_name.to_lowercase(),
        contact.id.to_lowercase()
    )
}

#[cfg(target_os = "macos")]
unsafe fn contact_from_objc(contact: *mut Object) -> Option<Contact> {
    if contact.is_null() {
        return None;
    }

    let identifier_ptr: *mut Object = msg_send![contact, identifier];
    let given_ptr: *mut Object = msg_send![contact, givenName];
    let family_ptr: *mut Object = msg_send![contact, familyName];
    let organization_ptr: *mut Object = msg_send![contact, organizationName];
    let phone_numbers_ptr: *mut Object = msg_send![contact, phoneNumbers];
    let email_addresses_ptr: *mut Object = msg_send![contact, emailAddresses];

    let identifier = nsstring_to_optional_string(identifier_ptr)?;
    let first_name = nsstring_to_optional_string(given_ptr);
    let last_name = nsstring_to_optional_string(family_ptr);
    let company_name = nsstring_to_optional_string(organization_ptr);
    let phone = first_phone_value(phone_numbers_ptr);
    let email = first_email_value(email_addresses_ptr);

    Some(Contact {
        id: identifier,
        first_name,
        last_name,
        company_name,
        phone,
        email,
    })
}

#[cfg(target_os = "macos")]
unsafe fn first_phone_value(phone_numbers: *mut Object) -> Option<String> {
    if phone_numbers.is_null() {
        return None;
    }

    let count: usize = msg_send![phone_numbers, count];
    for index in 0..count {
        let labeled_value: *mut Object = msg_send![phone_numbers, objectAtIndex: index];
        if labeled_value.is_null() {
            continue;
        }
        let phone_number: *mut Object = msg_send![labeled_value, value];
        if phone_number.is_null() {
            continue;
        }
        let phone_string: *mut Object = msg_send![phone_number, stringValue];
        if let Some(value) = nsstring_to_optional_string(phone_string) {
            return Some(value);
        }
    }

    None
}

#[cfg(target_os = "macos")]
unsafe fn first_email_value(email_addresses: *mut Object) -> Option<String> {
    if email_addresses.is_null() {
        return None;
    }

    let count: usize = msg_send![email_addresses, count];
    for index in 0..count {
        let labeled_value: *mut Object = msg_send![email_addresses, objectAtIndex: index];
        if labeled_value.is_null() {
            continue;
        }
        let email_value: *mut Object = msg_send![labeled_value, value];
        if let Some(value) = nsstring_to_optional_string(email_value) {
            return Some(value);
        }
    }

    None
}

#[cfg(target_os = "macos")]
unsafe fn nsstring_to_optional_string(ns_string: *mut Object) -> Option<String> {
    let value = nsstring_to_string(ns_string);
    let trimmed = value.trim();
    if trimmed.is_empty() {
        None
    } else {
        Some(trimmed.to_string())
    }
}

#[cfg(target_os = "macos")]
unsafe fn nsstring_to_string(ns_string: *mut Object) -> String {
    if ns_string.is_null() {
        return String::new();
    }
    let c_str: *const c_char = msg_send![ns_string, UTF8String];
    if c_str.is_null() {
        String::new()
    } else {
        CStr::from_ptr(c_str).to_string_lossy().into_owned()
    }
}

#[cfg(target_os = "macos")]
unsafe fn ns_error_to_string(error: *mut Object) -> String {
    if error.is_null() {
        return "Unknown contacts error.".into();
    }
    let description: *mut Object = msg_send![error, localizedDescription];
    let message = nsstring_to_string(description);
    if message.trim().is_empty() {
        "Unknown contacts error.".into()
    } else {
        message
    }
}

#[tauri::command]
fn resolve_download_output_path(base_name: String) -> Result<String, String> {
    if base_name.trim().is_empty() {
        return Err("Output filename cannot be empty.".into());
    }

    let base_path = Path::new(&base_name);
    if base_path.is_absolute() || base_path.components().count() > 1 {
        return Err("Output filename must not include directory segments.".into());
    }

    let home_dir = std::env::var("HOME")
        .map(PathBuf::from)
        .map_err(|_| "Could not resolve HOME directory.".to_string())?;
    let downloads_dir = home_dir.join("Downloads");

    let stem = base_path
        .file_stem()
        .and_then(|value| value.to_str())
        .filter(|value| !value.trim().is_empty())
        .ok_or_else(|| "Output filename is invalid.".to_string())?;

    let extension = base_path
        .extension()
        .and_then(|value| value.to_str())
        .filter(|value| !value.trim().is_empty())
        .unwrap_or("csv");

    let mut index: usize = 0;
    loop {
        let candidate_name = if index == 0 {
            format!("{stem}.{extension}")
        } else {
            format!("{stem}-{index}.{extension}")
        };
        let candidate_path = downloads_dir.join(candidate_name);
        if !candidate_path.exists() {
            return Ok(candidate_path.to_string_lossy().into_owned());
        }
        index += 1;
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_store::Builder::new().build())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            get_contacts,
            resolve_download_output_path
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
