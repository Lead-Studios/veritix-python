export class ApiResponseDto<T> {
  success: boolean;
  statusCode: number;
  data: T;
  timestamp: string;
  message?: string;

  constructor(
    success: boolean,
    statusCode: number,
    data: T,
    message?: string,
  ) {
    this.success = success;
    this.statusCode = statusCode;
    this.data = data;
    this.message = message;
    this.timestamp = new Date().toISOString();
  }
}

export class ErrorResponseDto {
  success: boolean = false;
  statusCode: number;
  message: string;
  error: string;
  timestamp: string;

  constructor(statusCode: number, message: string, error: string) {
    this.statusCode = statusCode;
    this.message = message;
    this.error = error;
    this.timestamp = new Date().toISOString();
  }
}
