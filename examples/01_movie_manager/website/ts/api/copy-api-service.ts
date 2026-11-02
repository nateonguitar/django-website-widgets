import { AppUrls } from "../app-urls";
import { ApiResult, ApiService, FieldErrorsResponse, MessageErrorResponse } from "./api-service";

/** ReportCopyRequestDto. */
export class ReportCopyRequest {
    kind = '';
    notes = '';
    unrecoverable = false;
}

/** ReportCopyResponseDto. */
export class ReportCopyResponse {
    report_id = 0;
    label = '';
    retired = false;
}

export type ReportCopyResult =
    | ApiResult<201, ReportCopyResponse>
    | ApiResult<400, FieldErrorsResponse>
    // Not out with the reporter, or already retired.
    | ApiResult<404, MessageErrorResponse>;

/** The copies router's endpoints, api/endpoints/copies/. */
export class CopyApiService extends ApiService {
    private static _instance: CopyApiService | null = null;

    /** The one CopyApiService; see MovieApiService.instance. */
    static get instance(): CopyApiService {
        CopyApiService._instance ??= new CopyApiService();
        return CopyApiService._instance;
    }

    private constructor() {
        super();
    }

    async reportCopy(label: string, report: ReportCopyRequest): Promise<ReportCopyResult> {
        // The URL arrives as /api/copies/{label}/reports.
        const url = AppUrls.endpoint_report_copy.replace('{label}', encodeURIComponent(label));
        return this._post<ReportCopyResult>(url, report, [201, 400, 404]);
    }
}
