export class HelperUtilities {
  /**
   * Generate a random token
   */
  static generateRandomToken(length: number = 32): string {
    const chars =
      'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  }

  /**
   * Format date to readable string
   */
  static formatDate(date: Date, format: string = 'YYYY-MM-DD'): string {
    return new Date(date).toLocaleDateString('en-US', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    });
  }

  /**
   * Calculate percentage
   */
  static calculatePercentage(current: number, total: number): number {
    if (total === 0) return 0;
    return Math.round((current / total) * 100);
  }

  /**
   * Paginate array
   */
  static paginate<T>(
    array: T[],
    page: number,
    pageSize: number,
  ): { data: T[]; total: number; page: number; pageSize: number } {
    const total = array.length;
    const start = (page - 1) * pageSize;
    const end = start + pageSize;
    return {
      data: array.slice(start, end),
      total,
      page,
      pageSize,
    };
  }

  /**
   * Sort array of objects
   */
  static sortBy<T>(
    array: T[],
    key: keyof T,
    order: 'asc' | 'desc' = 'asc',
  ): T[] {
    return [...array].sort((a, b) => {
      const valueA = a[key];
      const valueB = b[key];

      if (valueA < valueB) {
        return order === 'asc' ? -1 : 1;
      }
      if (valueA > valueB) {
        return order === 'asc' ? 1 : -1;
      }
      return 0;
    });
  }

  /**
   * Group array by property
   */
  static groupBy<T>(array: T[], key: keyof T): { [key: string]: T[] } {
    return array.reduce((result, item) => {
      const keyValue = String(item[key]);
      if (!result[keyValue]) {
        result[keyValue] = [];
      }
      result[keyValue].push(item);
      return result;
    }, {});
  }

  /**
   * Deep clone object
   */
  static deepClone<T>(obj: T): T {
    if (obj === null || typeof obj !== 'object') {
      return obj;
    }

    if (obj instanceof Date) {
      return new Date(obj.getTime()) as any;
    }

    if (obj instanceof Array) {
      const clonedArr = [];
      for (const element of obj) {
        clonedArr.push(this.deepClone(element));
      }
      return clonedArr as any;
    }

    if (obj instanceof Object) {
      const clonedObj = {};
      for (const key in obj) {
        if (obj.hasOwnProperty(key)) {
          clonedObj[key] = this.deepClone(obj[key]);
        }
      }
      return clonedObj as any;
    }
  }

  /**
   * Sleep for specified milliseconds
   */
  static sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

export class StringUtilities {
  /**
   * Generate slug from string
   */
  static generateSlug(str: string): string {
    return str
      .toLowerCase()
      .trim()
      .replace(/[^\w\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-');
  }

  /**
   * Capitalize first letter
   */
  static capitalize(str: string): string {
    return str.charAt(0).toUpperCase() + str.slice(1);
  }

  /**
   * Truncate string
   */
  static truncate(str: string, maxLength: number, suffix: string = '...'): string {
    if (str.length <= maxLength) {
      return str;
    }
    return str.slice(0, maxLength - suffix.length) + suffix;
  }
}
