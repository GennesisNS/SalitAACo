<?php

namespace SalitAACo\Models;

use Illuminate\Database\Eloquent\Model;

// Per-user customizations (editable images + recorded sounds), one row per (user_id, word).
class Customization extends Model
{
    protected $table = "customizations";

    // updated_at is maintained by MySQL (ON UPDATE CURRENT_TIMESTAMP).
    public $timestamps = false;

    protected $hidden = ["image_data", "sound_data"];
}
