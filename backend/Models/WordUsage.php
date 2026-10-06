<?php

namespace SalitAACo\Models;

use Illuminate\Database\Eloquent\Model;

// Per-user word usage counts (powers the "Madalas Gamitin" tab), one row per (user_id, word).
class WordUsage extends Model
{
    protected $table = "word_usage";

    // last_used is maintained by MySQL (ON UPDATE CURRENT_TIMESTAMP).
    public $timestamps = false;
}
